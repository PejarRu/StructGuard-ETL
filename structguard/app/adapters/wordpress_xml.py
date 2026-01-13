import json
import uuid
from typing import List

from lxml import etree

from .base import BaseAdapter


class WordPressXmlAdapter(BaseAdapter):
    """Adapter for WordPress XML export files using lxml for CDATA preservation."""

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
        Extract text segments from WordPress XML.
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

                # Generate unique ID
                element_id = str(uuid.uuid4())

                # Build context
                context = self._build_context(element)

                # Store element ID as attribute for later injection
                element.set("sg-id", element_id)

                extraction_items.append(
                    {
                        "id": element_id,
                        "context": context,
                        "original_text": text_content,
                        "edited_text": None,
                    }
                )

        # Serialize modified tree (now with sg-id attributes)
        # This modified skeleton should be returned to client for injection
        # For now, we only return the extraction JSON
        result = json.dumps(extraction_items, ensure_ascii=False, indent=2)
        return result.encode("utf-8")

    def inject(self, skeleton: bytes, modifications: bytes) -> bytes:
        """
        Inject modified text back into the WordPress XML skeleton.
        Returns reconstructed XML bytes.
        """
        parser = etree.XMLParser(strip_cdata=False, remove_blank_text=False)
        tree = etree.fromstring(skeleton, parser)

        # Load modifications
        modifications_data = json.loads(modifications.decode("utf-8"))
        modifications_map = {item["id"]: item for item in modifications_data}

        # Find all elements with sg-id attribute
        for element in tree.xpath(".//*[@sg-id]"):
            sg_id = element.get("sg-id")
            if sg_id in modifications_map:
                modification = modifications_map[sg_id]
                edited_text = modification.get("edited_text")

                # Only update if edited_text is provided
                if edited_text is not None:
                    self._set_text_content(element, edited_text)

            # Remove the sg-id attribute before final output
            element.attrib.pop("sg-id")

        # Serialize back to XML
        result = etree.tostring(
            tree, encoding="utf-8", xml_declaration=True, pretty_print=True
        )
        return result

    def _get_text_content(self, element) -> str:
        """Extract text from element, handling CDATA sections."""
        if element.text:
            return element.text
        return ""

    def _set_text_content(self, element, text: str):
        """Set text content of element, preserving CDATA if it was used."""
        # Check if original had CDATA
        # In lxml, CDATA is preserved in element.text when strip_cdata=False
        # We'll wrap the new content in CDATA if the tag typically uses it
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
