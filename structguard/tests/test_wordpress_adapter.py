import json
from pathlib import Path

import pytest
from lxml import etree

from app.adapters.wordpress_xml import WordPressXmlAdapter


@pytest.fixture
def wordpress_sample_file() -> bytes:
    """
    Load the real WordPress XML fixture file.
    Handles path resolution from both root and tests/ directory.
    """
    # Get the directory where this test file is located
    test_dir = Path(__file__).parent
    
    # Build path to the fixture file
    fixture_path = test_dir / "fixtures" / "serviciosvalepuertasvallasyherrerametlicaenvegabajatorreviejayguardamar.WordPress.2026-01-15.xml"
    
    if not fixture_path.exists():
        pytest.fail(f"Fixture file not found: {fixture_path}")
    
    with open(fixture_path, "rb") as f:
        return f.read()


@pytest.fixture
def adapter() -> WordPressXmlAdapter:
    """Return a fresh adapter instance."""
    return WordPressXmlAdapter()


class TestWordPressAdapterRealFile:
    """Test suite using the real WordPress export file."""
    
    def test_round_trip_integrity(self, adapter: WordPressXmlAdapter, wordpress_sample_file: bytes):
        """
        Test that extract -> modify -> inject preserves structure and CDATA.
        """
        # Step 1: Extract from real file
        extraction_result = adapter.extract(wordpress_sample_file)
        extraction_data = json.loads(extraction_result.decode("utf-8"))
        
        # Verify extraction is not empty and contains valid IDs
        assert len(extraction_data) > 0, "Extraction should return items"
        assert all("id" in item for item in extraction_data), "All items should have IDs"
        assert all(item["id"].startswith("/") for item in extraction_data), "IDs should be XPaths starting with /"
        
        # Step 2: Modify the first item
        test_string = "TEST_CHANGE_123_UNIQUE_MARKER"
        original_item = extraction_data[0].copy()
        original_id = original_item["id"]
        original_text = original_item["original_text"]
        
        # Create modified JSON
        extraction_data[0]["edited_text"] = test_string
        modified_json = json.dumps(extraction_data, ensure_ascii=False, indent=2).encode("utf-8")
        
        # Step 3: Inject back into the original file
        injected_result = adapter.inject(wordpress_sample_file, modified_json)
        
        # Step 4: Parse and verify the injected XML
        parser = etree.XMLParser(strip_cdata=False, remove_blank_text=False)
        injected_tree = etree.fromstring(injected_result, parser)
        original_tree = etree.fromstring(wordpress_sample_file, parser)
        
        # Find the modified element using XPath
        modified_elements = adapter._xpath_to_elements(injected_tree, original_id)
        assert len(modified_elements) == 1, f"Should find exactly one element for ID: {original_id}"
        modified_element = modified_elements[0]
        
        # Verify the text was changed correctly
        assert modified_element.text == test_string, f"Element text should be updated to '{test_string}'"
        
        # Step 5: Verify CDATA preservation
        # Check if the original element used CDATA
        original_elements = adapter._xpath_to_elements(original_tree, original_id)
        original_element = original_elements[0]
        
        # If the tag should use CDATA, verify it's present in output
        tag_name = modified_element.tag
        if tag_name in [
            "{http://purl.org/rss/1.0/modules/content/}encoded",
            "{http://wordpress.org/export/1.2/excerpt/}encoded",
        ]:
            # Serialize just this element to check CDATA
            element_str = etree.tostring(modified_element, encoding="unicode")
            assert "<![CDATA[" in element_str, f"CDATA should be preserved for tag {tag_name}"
            assert test_string in element_str, "Test string should be in CDATA section"
        
        # Step 6: Verify structural integrity - count of all elements should be the same
        original_all_elements = original_tree.xpath("//*")
        injected_all_elements = injected_tree.xpath("//*")
        assert len(original_all_elements) == len(injected_all_elements), "Element count should remain the same"
        
        # Verify all other extracted items remain unchanged
        for i, item in enumerate(extraction_data[1:], start=1):
            item_id = item["id"]
            elements = adapter._xpath_to_elements(injected_tree, item_id)
            if elements:
                # These should have original text (since we didn't modify them)
                assert elements[0].text == item["original_text"], f"Unmodified item {i} should retain original text"
    
    def test_validate_with_valid_modifications(self, adapter: WordPressXmlAdapter, wordpress_sample_file: bytes):
        """
        Test validation with valid modifications returns 'valid' status.
        """
        # Extract to get valid structure
        extraction_result = adapter.extract(wordpress_sample_file)
        extraction_data = json.loads(extraction_result.decode("utf-8"))
        
        # Modify one item
        if len(extraction_data) > 0:
            extraction_data[0]["edited_text"] = "Valid modification"
        
        modified_json = json.dumps(extraction_data, ensure_ascii=False, indent=2).encode("utf-8")
        
        # Validate
        validation_result = adapter.validate(wordpress_sample_file, modified_json)
        
        # Assertions
        assert validation_result["status"] == "valid", "Validation should pass with valid modifications"
        assert validation_result["diff_stats"]["total_items"] == len(extraction_data)
        assert validation_result["diff_stats"]["modified_items"] == 1
        assert len(validation_result["changes"]) == 1
        assert validation_result["changes"][0]["new_text"] == "Valid modification"
        assert len(validation_result["errors"]) == 0
    
    def test_validate_with_unknown_id(self, adapter: WordPressXmlAdapter, wordpress_sample_file: bytes):
        """
        Test validation with non-existent ID returns 'error' status.
        """
        # Create fake modification with invalid ID
        fake_modifications = [
            {
                "id": "/rss/channel/fake_node[999]",
                "context": "Fake context",
                "original_text": "This doesn't exist",
                "edited_text": "Trying to inject into fake location"
            }
        ]
        
        fake_json = json.dumps(fake_modifications, ensure_ascii=False, indent=2).encode("utf-8")
        
        # Validate
        validation_result = adapter.validate(wordpress_sample_file, fake_json)
        
        # Assertions
        assert validation_result["status"] == "error", "Validation should fail with unknown ID"
        assert validation_result["diff_stats"]["unknown_ids"] > 0
        assert len(validation_result["errors"]) > 0
        
        # Check for the specific error
        unknown_id_errors = [e for e in validation_result["errors"] if e.get("error") == "unknown_id"]
        assert len(unknown_id_errors) > 0, "Should have at least one unknown_id error"
        assert unknown_id_errors[0]["id"] == "/rss/channel/fake_node[999]"
    
    def test_validate_with_missing_modifications(self, adapter: WordPressXmlAdapter, wordpress_sample_file: bytes):
        """
        Test validation when modifications JSON is missing some IDs from skeleton.
        """
        # Extract to get valid structure
        extraction_result = adapter.extract(wordpress_sample_file)
        extraction_data = json.loads(extraction_result.decode("utf-8"))
        
        # Only include first half of items (simulating incomplete modifications)
        if len(extraction_data) > 2:
            partial_modifications = extraction_data[:len(extraction_data) // 2]
        else:
            partial_modifications = extraction_data[:1]
        
        partial_json = json.dumps(partial_modifications, ensure_ascii=False, indent=2).encode("utf-8")
        
        # Validate
        validation_result = adapter.validate(wordpress_sample_file, partial_json)
        
        # Assertions
        assert validation_result["status"] == "error", "Should detect missing modifications"
        assert validation_result["diff_stats"]["missing_modifications"] > 0
        
        # Check for missing_modification errors
        missing_errors = [e for e in validation_result["errors"] if e.get("error") == "missing_modification"]
        assert len(missing_errors) > 0, "Should have missing_modification errors"
    
    def test_extraction_includes_all_safe_zones(self, adapter: WordPressXmlAdapter, wordpress_sample_file: bytes):
        """
        Test that extraction finds all expected Safe Zone elements.
        """
        extraction_result = adapter.extract(wordpress_sample_file)
        extraction_data = json.loads(extraction_result.decode("utf-8"))
        
        # Parse original to count expected elements
        parser = etree.XMLParser(strip_cdata=False, remove_blank_text=False)
        tree = etree.fromstring(wordpress_sample_file, parser)
        
        expected_count = 0
        for xpath_pattern in adapter.SAFE_ZONES:
            elements = tree.xpath(xpath_pattern, namespaces=adapter.NAMESPACES)
            for element in elements:
                text_content = adapter._get_text_content(element)
                if text_content and text_content.strip():
                    expected_count += 1
        
        assert len(extraction_data) == expected_count, f"Should extract {expected_count} items from Safe Zones"
    
    def test_xpath_id_format(self, adapter: WordPressXmlAdapter, wordpress_sample_file: bytes):
        """
        Test that XPath IDs have the correct format from tree.getpath().
        """
        extraction_result = adapter.extract(wordpress_sample_file)
        extraction_data = json.loads(extraction_result.decode("utf-8"))
        
        for item in extraction_data:
            xpath_id = item["id"]
            
            # XPath should start with /
            assert xpath_id.startswith("/"), f"XPath should start with /: {xpath_id}"
            
            # Should contain element indices like [1], [2], etc.
            assert "[" in xpath_id and "]" in xpath_id, f"XPath should contain indices: {xpath_id}"
    
    def test_inject_handles_empty_edited_text(self, adapter: WordPressXmlAdapter, wordpress_sample_file: bytes):
        """
        Test that inject skips items without edited_text.
        """
        # Extract
        extraction_result = adapter.extract(wordpress_sample_file)
        extraction_data = json.loads(extraction_result.decode("utf-8"))
        
        # Don't set edited_text on any items (leave as None)
        modified_json = json.dumps(extraction_data, ensure_ascii=False, indent=2).encode("utf-8")
        
        # Inject (should not modify anything)
        injected_result = adapter.inject(wordpress_sample_file, modified_json)
        
        # Parse both
        parser = etree.XMLParser(strip_cdata=False, remove_blank_text=False)
        original_tree = etree.fromstring(wordpress_sample_file, parser)
        injected_tree = etree.fromstring(injected_result, parser)
        
        # Compare - should be identical
        for item in extraction_data:
            item_id = item["id"]
            original_elements = adapter._xpath_to_elements(original_tree, item_id)
            injected_elements = adapter._xpath_to_elements(injected_tree, item_id)
            
            if original_elements and injected_elements:
                assert original_elements[0].text == injected_elements[0].text, \
                    "Text should be unchanged when edited_text is None"
    
    def test_validate_with_malformed_json(self, adapter: WordPressXmlAdapter, wordpress_sample_file: bytes):
        """
        Test that validation handles malformed JSON gracefully.
        """
        malformed_json = b"{ this is not valid json }"
        
        validation_result = adapter.validate(wordpress_sample_file, malformed_json)
        
        assert validation_result["status"] == "error"
        assert len(validation_result["errors"]) > 0
        assert validation_result["errors"][0]["error"] == "invalid_json"
    
    def test_validate_with_malformed_xml(self, adapter: WordPressXmlAdapter):
        """
        Test that validation handles malformed XML gracefully.
        """
        malformed_xml = b"<xml><broken>"
        valid_json = json.dumps([{"id": "/test", "edited_text": "test"}]).encode("utf-8")
        
        validation_result = adapter.validate(malformed_xml, valid_json)
        
        assert validation_result["status"] == "error"
        assert len(validation_result["errors"]) > 0
        assert validation_result["errors"][0]["error"] == "invalid_xml"


class TestWordPressAdapterEdgeCases:
    """Test edge cases and error handling."""
    
    def test_extract_empty_xml(self, adapter: WordPressXmlAdapter):
        """Test extraction with minimal XML."""
        minimal_xml = b'<?xml version="1.0"?><root></root>'
        
        result = adapter.extract(minimal_xml)
        data = json.loads(result.decode("utf-8"))
        
        assert isinstance(data, list)
        assert len(data) == 0, "Should return empty list for XML with no Safe Zones"
    
    def test_inject_preserves_xml_declaration(self, adapter: WordPressXmlAdapter, wordpress_sample_file: bytes):
        """Test that XML declaration is preserved after injection."""
        # Extract
        extraction_result = adapter.extract(wordpress_sample_file)
        extraction_data = json.loads(extraction_result.decode("utf-8"))
        
        if extraction_data:
            extraction_data[0]["edited_text"] = "Modified"
        
        modified_json = json.dumps(extraction_data, ensure_ascii=False, indent=2).encode("utf-8")
        
        # Inject
        injected_result = adapter.inject(wordpress_sample_file, modified_json)
        injected_str = injected_result.decode("utf-8")
        
        # Check for XML declaration
        assert injected_str.startswith("<?xml"), "Should preserve XML declaration"
        assert 'version="1.0"' in injected_str or "version='1.0'" in injected_str
