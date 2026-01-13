"""
Tests for StructGuard-API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestRootEndpoint:
    """Test the root endpoint"""
    
    def test_root(self):
        """Test root endpoint returns API information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "StructGuard-API"
        assert "/extract" in data["endpoints"]
        assert "/inject" in data["endpoints"]


class TestXMLExtractInject:
    """Test XML extract and inject operations"""
    
    def test_simple_xml_extract(self):
        """Test extracting text from simple XML"""
        xml_content = """<?xml version="1.0"?>
<root>
    <title>Hello World</title>
    <description>This is a test</description>
</root>"""
        
        response = client.post(
            "/extract",
            json={"content": xml_content, "format": "xml"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "flat_map" in data
        assert "metadata" in data
        
        flat_map = data["flat_map"]
        assert len(flat_map) == 2
        assert "Hello World" in flat_map.values()
        assert "This is a test" in flat_map.values()
    
    def test_xml_extract_inject_roundtrip(self):
        """Test that extract + inject preserves XML structure"""
        xml_content = """<?xml version="1.0"?>
<root>
    <title>Original Title</title>
    <content>Original content</content>
</root>"""
        
        # Extract
        extract_response = client.post(
            "/extract",
            json={"content": xml_content, "format": "xml"}
        )
        assert extract_response.status_code == 200
        extract_data = extract_response.json()
        
        # Modify flat map
        flat_map = extract_data["flat_map"]
        for key, value in flat_map.items():
            if value == "Original Title":
                flat_map[key] = "Modified Title"
            elif value == "Original content":
                flat_map[key] = "Modified content"
        
        # Inject
        inject_response = client.post(
            "/inject",
            json={
                "flat_map": flat_map,
                "metadata": extract_data["metadata"],
                "format": "xml"
            }
        )
        
        assert inject_response.status_code == 200
        result = inject_response.json()
        reconstructed = result["content"]
        
        # Verify structure is preserved and content is updated
        assert "Modified Title" in reconstructed
        assert "Modified content" in reconstructed
        assert "<title>" in reconstructed
        assert "<content>" in reconstructed
        assert "Original Title" not in reconstructed
        assert "Original content" not in reconstructed
    
    def test_nested_xml_extract(self):
        """Test extracting text from nested XML"""
        xml_content = """<root>
    <section>
        <heading>Section 1</heading>
        <paragraph>First paragraph</paragraph>
        <paragraph>Second paragraph</paragraph>
    </section>
</root>"""
        
        response = client.post(
            "/extract",
            json={"content": xml_content, "format": "xml"}
        )
        
        assert response.status_code == 200
        data = response.json()
        flat_map = data["flat_map"]
        
        assert len(flat_map) == 3
        values = list(flat_map.values())
        assert "Section 1" in values
        assert "First paragraph" in values
        assert "Second paragraph" in values
    
    def test_xml_with_attributes(self):
        """Test XML with attributes"""
        xml_content = """<root>
    <item id="1" type="text">First item</item>
    <item id="2" type="text">Second item</item>
</root>"""
        
        response = client.post(
            "/extract",
            json={"content": xml_content, "format": "xml"}
        )
        
        assert response.status_code == 200
        data = response.json()
        flat_map = data["flat_map"]
        
        assert "First item" in flat_map.values()
        assert "Second item" in flat_map.values()
    
    def test_invalid_xml(self):
        """Test handling of invalid XML"""
        invalid_xml = "<root><unclosed>"
        
        response = client.post(
            "/extract",
            json={"content": invalid_xml, "format": "xml"}
        )
        
        assert response.status_code == 400
        assert "Invalid XML" in response.json()["detail"]


class TestJSONExtractInject:
    """Test JSON extract and inject operations"""
    
    def test_simple_json_extract(self):
        """Test extracting text from simple JSON"""
        json_content = '{"title": "Hello World", "description": "This is a test"}'
        
        response = client.post(
            "/extract",
            json={"content": json_content, "format": "json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "flat_map" in data
        assert "metadata" in data
        
        flat_map = data["flat_map"]
        assert len(flat_map) == 2
        assert "Hello World" in flat_map.values()
        assert "This is a test" in flat_map.values()
    
    def test_json_extract_inject_roundtrip(self):
        """Test that extract + inject preserves JSON structure"""
        json_content = '{"title": "Original Title", "content": "Original content", "count": 42}'
        
        # Extract
        extract_response = client.post(
            "/extract",
            json={"content": json_content, "format": "json"}
        )
        assert extract_response.status_code == 200
        extract_data = extract_response.json()
        
        # Modify flat map
        flat_map = extract_data["flat_map"]
        for key, value in flat_map.items():
            if value == "Original Title":
                flat_map[key] = "Modified Title"
            elif value == "Original content":
                flat_map[key] = "Modified content"
        
        # Inject
        inject_response = client.post(
            "/inject",
            json={
                "flat_map": flat_map,
                "metadata": extract_data["metadata"],
                "format": "json"
            }
        )
        
        assert inject_response.status_code == 200
        result = inject_response.json()
        reconstructed = result["content"]
        
        # Verify structure is preserved and content is updated
        assert "Modified Title" in reconstructed
        assert "Modified content" in reconstructed
        assert '"count": 42' in reconstructed or '"count":42' in reconstructed
        assert "Original Title" not in reconstructed
    
    def test_nested_json_extract(self):
        """Test extracting text from nested JSON"""
        json_content = '''
        {
            "article": {
                "title": "Article Title",
                "sections": [
                    {"heading": "Section 1", "text": "Content 1"},
                    {"heading": "Section 2", "text": "Content 2"}
                ]
            }
        }
        '''
        
        response = client.post(
            "/extract",
            json={"content": json_content, "format": "json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        flat_map = data["flat_map"]
        
        assert len(flat_map) == 5
        values = list(flat_map.values())
        assert "Article Title" in values
        assert "Section 1" in values
        assert "Content 1" in values
        assert "Section 2" in values
        assert "Content 2" in values
    
    def test_json_with_arrays(self):
        """Test JSON with arrays"""
        json_content = '{"items": ["First", "Second", "Third"]}'
        
        response = client.post(
            "/extract",
            json={"content": json_content, "format": "json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        flat_map = data["flat_map"]
        
        assert len(flat_map) == 3
        assert "First" in flat_map.values()
        assert "Second" in flat_map.values()
        assert "Third" in flat_map.values()
    
    def test_invalid_json(self):
        """Test handling of invalid JSON"""
        invalid_json = '{"unclosed": '
        
        response = client.post(
            "/extract",
            json={"content": invalid_json, "format": "json"}
        )
        
        assert response.status_code == 400
        assert "Invalid JSON" in response.json()["detail"]


class TestErrorHandling:
    """Test error handling"""
    
    def test_unsupported_format_extract(self):
        """Test unsupported format in extract"""
        response = client.post(
            "/extract",
            json={"content": "some content", "format": "yaml"}
        )
        
        assert response.status_code == 400
        assert "Unsupported format" in response.json()["detail"]
    
    def test_unsupported_format_inject(self):
        """Test unsupported format in inject"""
        response = client.post(
            "/inject",
            json={
                "flat_map": {},
                "metadata": {},
                "format": "yaml"
            }
        )
        
        assert response.status_code == 400
        assert "Unsupported format" in response.json()["detail"]
    
    def test_missing_fields(self):
        """Test missing required fields"""
        response = client.post(
            "/extract",
            json={"content": "test"}
        )
        
        assert response.status_code == 422  # Validation error


class TestComplexScenarios:
    """Test complex real-world scenarios"""
    
    def test_xml_with_mixed_content(self):
        """Test XML with mixed text and element content"""
        xml_content = """<article>
    <p>This is <bold>important</bold> text.</p>
</article>"""
        
        response = client.post(
            "/extract",
            json={"content": xml_content, "format": "xml"}
        )
        
        assert response.status_code == 200
        data = response.json()
        flat_map = data["flat_map"]
        
        # Should extract both the text before <bold> and the bold text
        assert len(flat_map) >= 1
    
    def test_large_json_structure(self):
        """Test handling of larger JSON structures"""
        json_content = '''
        {
            "document": {
                "metadata": {
                    "title": "Large Document",
                    "author": "Test Author",
                    "date": "2024-01-01"
                },
                "chapters": [
                    {
                        "number": 1,
                        "title": "Introduction",
                        "paragraphs": ["First para", "Second para"]
                    },
                    {
                        "number": 2,
                        "title": "Main Content",
                        "paragraphs": ["Third para", "Fourth para"]
                    }
                ]
            }
        }
        '''
        
        # Extract
        extract_response = client.post(
            "/extract",
            json={"content": json_content, "format": "json"}
        )
        assert extract_response.status_code == 200
        extract_data = extract_response.json()
        
        # Inject without modifications
        inject_response = client.post(
            "/inject",
            json={
                "flat_map": extract_data["flat_map"],
                "metadata": extract_data["metadata"],
                "format": "json"
            }
        )
        assert inject_response.status_code == 200
