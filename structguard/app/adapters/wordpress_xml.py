import json
from typing import List

from lxml import etree

from .base import BaseAdapter


class WordPressXmlAdapter(BaseAdapter):
    """
    Adapter for WordPress XML export files using lxml for CDATA preservation.
    Uses deterministic XPath-based IDs for stateless operation.
    """

    # WordPress XML namespaces
    NAMESPACES = {
        "content": "http://purl.org/rss/1.0/modules/content/",
        "wp": "http://wordpress.org/export/1.2/",
        "excerpt": "http://wordpress.org/export/1.2/excerpt/",
    }

    # XPath patterns for extracting editable content
    SAFE_ZONES = [
        ".//title",
        ".//content:encoded",
        ".//excerpt:encoded",
        ".//wp:meta_value",
    ]

    def extract(self, source: bytes) -> bytes:
        """
        Extract text segments from WordPress XML using deterministic XPath IDs.
        Returns JSON bytes containing extraction schema.
        """
        parser = etree.XMLParser(strip_cdata=False, remove_blank_text=False)
        tree = etree.fromstring(source, parser)

        extraction_items = []

        for xpath_pattern in self.SAFE_ZONES:
            elements = tree.xpath(xpath_pattern, namespaces=self.NAMESPACES)
            for element in elements:
                # Get text content
                text_content = self._get_text_content(element)
                if not text_content or not text_content.strip():
                    continue

                # Generate deterministic XPath ID using tree.getpath()
                element_id = tree.getpath(element)

                # Build context
                context = self._build_context(element)

                extraction_items.append(
                    {
                        "id": element_id,
                        "context": context,
                        "original_text": text_content,
                        "edited_text": None,
                    }
                )

        # Return extraction JSON only (no tree modification)
        result = json.dumps(extraction_items, ensure_ascii=False, indent=2)
        return result.encode("utf-8")

    def inject(self, skeleton: bytes, modifications: bytes) -> bytes:
        """
        Inject modified text back into the CLEAN WordPress XML skeleton using XPath IDs.
        Returns reconstructed XML bytes.
        """
        parser = etree.XMLParser(strip_cdata=False, remove_blank_text=False)
        tree = etree.fromstring(skeleton, parser)

        # Load modifications
        modifications_data = json.loads(modifications.decode("utf-8"))
        
        for item in modifications_data:
            xpath_id = item.get("id")
            edited_text = item.get("edited_text")

            # Skip if no edited text or no ID
            if edited_text is None or not xpath_id:
                continue

            # Find element using the XPath ID
            elements = self._xpath_to_elements(tree, xpath_id)
            
            if not elements:
                # Element not found, skip
                continue
            
            if len(elements) > 1:
                # Multiple elements found (shouldn't happen with getpath), use first
                pass
            
            element = elements[0]
            self._set_text_content(element, edited_text)

        # Serialize back to XML
        result = etree.tostring(
            tree, encoding="utf-8", xml_declaration=True, pretty_print=True
        )
        return result

    def _xpath_to_elements(self, tree, xpath_str: str) -> List:
        """
        Convert an XPath string (from getpath) back to elements.
        Handles namespace resolution between getpath format and xpath format.
        """
        # getpath returns XPath with {namespace}tag format
        # We need to convert it to use namespace prefixes for xpath()
        
        # First, try direct xpath (works for paths without namespaces)
        try:
            result = tree.xpath(xpath_str)
            if result:
                return result
        except etree.XPathEvalError:
            pass
        
        # If that fails, convert {http://...}tag to prefix:tag format
        converted_xpath = xpath_str
        for prefix, uri in self.NAMESPACES.items():
            converted_xpath = converted_xpath.replace(f'{{{uri}}}', f'{prefix}:')
        
        try:
            return tree.xpath(converted_xpath, namespaces=self.NAMESPACES)
        except etree.XPathEvalError:
            # XPath evaluation failed, return empty list
            return []

    def _get_text_content(self, element) -> str:
        """Extract text from element, handling CDATA sections."""
        if element.text:
            return element.text
        return ""

    def _set_text_content(self, element, text: str):
        """Set text content of element, preserving CDATA if it was used."""
        # Wrap the new content in CDATA if the tag typically uses it
        if element.tag in [
            "{http://purl.org/rss/1.0/modules/content/}encoded",
            "{http://wordpress.org/export/1.2/excerpt/}encoded",
        ]:
            # Use CDATA for these elements
            element.text = etree.CDATA(text)
        else:
            element.text = text

    def _build_context(self, element) -> str:
        """Build a context string for the element."""
        tag_name = etree.QName(element).localname
        
        # Try to find parent item title for context
        parent_item = element.xpath("ancestor::item[1]")
        if parent_item:
            title_elem = parent_item[0].find("title")
            if title_elem is not None and title_elem.text:
                return f"{tag_name} in: {title_elem.text[:50]}"
        
        return f"{tag_name}"

    def validate(self, skeleton: bytes, modifications: bytes) -> dict:
        """
        Validate modifications against skeleton structure.
        
        Returns a dictionary with:
        - status: "valid" or "error"
        - diff_stats: Statistics about changes
        - changes: List of actual changes
        - errors: List of validation errors (if any)
        """
        errors = []
        changes = []
        
        try:
            # Parse skeleton to get all valid XPath IDs
            parser = etree.XMLParser(strip_cdata=False, remove_blank_text=False)
            tree = etree.fromstring(skeleton, parser)
            
            # Extract all valid XPaths from skeleton
            valid_xpaths = set()
            xpath_to_content = {}
            xpath_to_context = {}
            
            for xpath_pattern in self.SAFE_ZONES:
                elements = tree.xpath(xpath_pattern, namespaces=self.NAMESPACES)
                for element in elements:
                    text_content = self._get_text_content(element)
                    if not text_content or not text_content.strip():
                        continue
                    
                    element_id = tree.getpath(element)
                    valid_xpaths.add(element_id)
                    xpath_to_content[element_id] = text_content
                    xpath_to_context[element_id] = self._build_context(element)
            
            # Parse modifications
            modifications_data = json.loads(modifications.decode("utf-8"))
            
            # Track modification IDs
            modification_ids = set()
            changed_count = 0
            
            for item in modifications_data:
                item_id = item.get("id")
                edited_text = item.get("edited_text")
                original_text = item.get("original_text", "")
                
                if not item_id:
                    errors.append({"error": "missing_id", "item": item})
                    continue
                
                modification_ids.add(item_id)
                
                # Check if ID exists in skeleton
                if item_id not in valid_xpaths:
                    errors.append({
                        "error": "unknown_id",
                        "id": item_id,
                        "message": f"ID not found in skeleton: {item_id}"
                    })
                    continue
                
                # Check if content has actually changed
                skeleton_content = xpath_to_content.get(item_id, "")
                
                # Only track changes if edited_text is provided and different
                if edited_text is not None and edited_text != skeleton_content:
                    changed_count += 1
                    changes.append({
                        "id": item_id,
                        "context": xpath_to_context.get(item_id, ""),
                        "original_text": skeleton_content,
                        "new_text": edited_text
                    })
            
            # Check for missing IDs (IDs in skeleton but not in modifications)
            missing_ids = valid_xpaths - modification_ids
            if missing_ids:
                for missing_id in missing_ids:
                    errors.append({
                        "error": "missing_modification",
                        "id": missing_id,
                        "message": f"Skeleton element has no corresponding modification: {missing_id}"
                    })
            
            # Determine status
            status = "valid" if not errors else "error"
            
            return {
                "status": status,
                "diff_stats": {
                    "total_items": len(valid_xpaths),
                    "modified_items": changed_count,
                    "unchanged_items": len(valid_xpaths) - changed_count,
                    "modifications_provided": len(modification_ids),
                    "missing_modifications": len(missing_ids),
                    "unknown_ids": sum(1 for e in errors if e.get("error") == "unknown_id")
                },
                "changes": changes,
                "errors": errors
            }
            
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "diff_stats": {
                    "total_items": 0,
                    "modified_items": 0,
                    "unchanged_items": 0,
                    "modifications_provided": 0,
                    "missing_modifications": 0,
                    "unknown_ids": 0
                },
                "changes": [],
                "errors": [{"error": "invalid_json", "message": str(e)}]
            }
        except etree.XMLSyntaxError as e:
            return {
                "status": "error",
                "diff_stats": {
                    "total_items": 0,
                    "modified_items": 0,
                    "unchanged_items": 0,
                    "modifications_provided": 0,
                    "missing_modifications": 0,
                    "unknown_ids": 0
                },
                "changes": [],
                "errors": [{"error": "invalid_xml", "message": str(e)}]
            }
        except Exception as e:
            return {
                "status": "error",
                "diff_stats": {
                    "total_items": 0,
                    "modified_items": 0,
                    "unchanged_items": 0,
                    "modifications_provided": 0,
                    "missing_modifications": 0,
                    "unknown_ids": 0
                },
                "changes": [],
                "errors": [{"error": "unknown", "message": str(e)}]
            }
        
        return f"{tag_name}"
