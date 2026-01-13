"""
Example usage of StructGuard-API with XML documents
"""

import requests
import json

# Base URL - adjust if running on different host/port
BASE_URL = "http://localhost:8000"


def example_basic_xml():
    """Basic XML extraction and injection example"""
    print("=" * 60)
    print("EXAMPLE 1: Basic XML Extract and Inject")
    print("=" * 60)
    
    # Original XML content
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<article>
    <title>The Future of AI</title>
    <author>John Doe</author>
    <content>
        <paragraph>Artificial intelligence is transforming our world.</paragraph>
        <paragraph>Machine learning models are becoming more powerful.</paragraph>
    </content>
</article>"""
    
    print("\n1. Original XML:")
    print(xml_content)
    
    # Step 1: Extract
    print("\n2. Extracting text content...")
    extract_response = requests.post(
        f"{BASE_URL}/extract",
        json={"content": xml_content, "format": "xml"}
    )
    
    if extract_response.status_code != 200:
        print(f"Error: {extract_response.text}")
        return
    
    extract_data = extract_response.json()
    flat_map = extract_data["flat_map"]
    metadata = extract_data["metadata"]
    
    print(f"\n3. Extracted flat map ({len(flat_map)} text nodes):")
    for key, value in flat_map.items():
        print(f"   {key}: {value[:50]}..." if len(value) > 50 else f"   {key}: {value}")
    
    # Step 2: Edit the content (simulate LLM editing)
    print("\n4. Editing content (converting to uppercase)...")
    edited_map = {}
    for key, value in flat_map.items():
        edited_map[key] = value.upper()
    
    # Step 3: Inject
    print("\n5. Injecting edited content back...")
    inject_response = requests.post(
        f"{BASE_URL}/inject",
        json={
            "flat_map": edited_map,
            "metadata": metadata,
            "format": "xml"
        }
    )
    
    if inject_response.status_code != 200:
        print(f"Error: {inject_response.text}")
        return
    
    result = inject_response.json()
    reconstructed = result["content"]
    
    print("\n6. Reconstructed XML:")
    print(reconstructed)
    
    print("\n✓ Structure preserved, content modified!")


def example_translation_workflow():
    """Simulate a translation workflow"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Translation Workflow")
    print("=" * 60)
    
    xml_content = """<blog>
    <post id="1">
        <title>Hello World</title>
        <body>This is my first blog post.</body>
    </post>
    <post id="2">
        <title>Second Post</title>
        <body>Here is some more content.</body>
    </post>
</blog>"""
    
    print("\n1. Original English XML:")
    print(xml_content)
    
    # Extract
    extract_response = requests.post(
        f"{BASE_URL}/extract",
        json={"content": xml_content, "format": "xml"}
    )
    
    extract_data = extract_response.json()
    flat_map = extract_data["flat_map"]
    
    # Simulate translation (English to Spanish)
    translations = {
        "Hello World": "Hola Mundo",
        "This is my first blog post.": "Esta es mi primera publicación de blog.",
        "Second Post": "Segunda Publicación",
        "Here is some more content.": "Aquí hay más contenido."
    }
    
    print("\n2. Translating text nodes...")
    translated_map = {}
    for key, value in flat_map.items():
        translated_map[key] = translations.get(value, value)
        print(f"   '{value}' → '{translated_map[key]}'")
    
    # Inject
    inject_response = requests.post(
        f"{BASE_URL}/inject",
        json={
            "flat_map": translated_map,
            "metadata": extract_data["metadata"],
            "format": "xml"
        }
    )
    
    result = inject_response.json()
    print("\n3. Translated XML:")
    print(result["content"])


def example_content_enrichment():
    """Example of enriching content with additional information"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Content Enrichment")
    print("=" * 60)
    
    xml_content = """<product>
    <name>Laptop</name>
    <description>Fast computer</description>
    <price>999</price>
</product>"""
    
    print("\n1. Original product XML:")
    print(xml_content)
    
    # Extract
    extract_response = requests.post(
        f"{BASE_URL}/extract",
        json={"content": xml_content, "format": "xml"}
    )
    
    extract_data = extract_response.json()
    flat_map = extract_data["flat_map"]
    
    # Enrich content
    print("\n2. Enriching content...")
    enriched_map = {}
    for key, value in flat_map.items():
        if "Laptop" in value:
            enriched_map[key] = "Premium Laptop - High Performance Computing Device"
        elif "Fast computer" in value:
            enriched_map[key] = "Ultra-fast computer with cutting-edge technology and superior performance"
        else:
            enriched_map[key] = value
        
        if enriched_map[key] != value:
            print(f"   Enriched: '{value}' → '{enriched_map[key]}'")
    
    # Inject
    inject_response = requests.post(
        f"{BASE_URL}/inject",
        json={
            "flat_map": enriched_map,
            "metadata": extract_data["metadata"],
            "format": "xml"
        }
    )
    
    result = inject_response.json()
    print("\n3. Enriched XML:")
    print(result["content"])


def main():
    """Run all examples"""
    print("\n" + "🔒 StructGuard-API Examples - XML" + "\n")
    print("Make sure the API server is running on http://localhost:8000")
    print("Start it with: python main.py")
    input("\nPress Enter to continue...")
    
    try:
        # Test connection
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ Cannot connect to API server!")
            return
        
        print("✓ Connected to API server\n")
        
        # Run examples
        example_basic_xml()
        example_translation_workflow()
        example_content_enrichment()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API server!")
        print("Make sure the server is running: python main.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
