"""
Example usage of StructGuard-API with JSON documents
"""

import requests
import json

# Base URL - adjust if running on different host/port
BASE_URL = "http://localhost:8000"


def example_basic_json():
    """Basic JSON extraction and injection example"""
    print("=" * 60)
    print("EXAMPLE 1: Basic JSON Extract and Inject")
    print("=" * 60)
    
    # Original JSON content
    json_content = {
        "user": {
            "name": "Alice Smith",
            "bio": "Software developer and tech enthusiast",
            "location": "San Francisco"
        },
        "posts": [
            {
                "title": "Getting Started with Python",
                "content": "Python is a great language for beginners."
            },
            {
                "title": "Advanced FastAPI",
                "content": "FastAPI makes building APIs incredibly fast."
            }
        ]
    }
    
    json_string = json.dumps(json_content, indent=2)
    
    print("\n1. Original JSON:")
    print(json_string)
    
    # Step 1: Extract
    print("\n2. Extracting text content...")
    extract_response = requests.post(
        f"{BASE_URL}/extract",
        json={"content": json_string, "format": "json"}
    )
    
    if extract_response.status_code != 200:
        print(f"Error: {extract_response.text}")
        return
    
    extract_data = extract_response.json()
    flat_map = extract_data["flat_map"]
    metadata = extract_data["metadata"]
    
    print(f"\n3. Extracted flat map ({len(flat_map)} text values):")
    for key, value in flat_map.items():
        print(f"   {key}: {value}")
    
    # Step 2: Edit the content
    print("\n4. Editing content (adding emoji)...")
    edited_map = {}
    for key, value in flat_map.items():
        edited_map[key] = f"✨ {value}"
    
    # Step 3: Inject
    print("\n5. Injecting edited content back...")
    inject_response = requests.post(
        f"{BASE_URL}/inject",
        json={
            "flat_map": edited_map,
            "metadata": metadata,
            "format": "json"
        }
    )
    
    if inject_response.status_code != 200:
        print(f"Error: {inject_response.text}")
        return
    
    result = inject_response.json()
    reconstructed = result["content"]
    
    print("\n6. Reconstructed JSON:")
    print(reconstructed)
    
    print("\n✓ Structure preserved, content modified!")


def example_multilingual_content():
    """Simulate multilingual content management"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Multilingual Content Management")
    print("=" * 60)
    
    json_content = {
        "page": {
            "title": "Welcome",
            "subtitle": "Discover our services",
            "sections": [
                {
                    "heading": "About Us",
                    "text": "We are a technology company"
                },
                {
                    "heading": "Contact",
                    "text": "Get in touch with our team"
                }
            ]
        }
    }
    
    json_string = json.dumps(json_content, indent=2)
    
    print("\n1. Original English JSON:")
    print(json_string)
    
    # Extract
    extract_response = requests.post(
        f"{BASE_URL}/extract",
        json={"content": json_string, "format": "json"}
    )
    
    extract_data = extract_response.json()
    flat_map = extract_data["flat_map"]
    
    # Translate to French
    translations = {
        "Welcome": "Bienvenue",
        "Discover our services": "Découvrez nos services",
        "About Us": "À Propos",
        "We are a technology company": "Nous sommes une entreprise technologique",
        "Contact": "Contact",
        "Get in touch with our team": "Contactez notre équipe"
    }
    
    print("\n2. Translating to French...")
    translated_map = {}
    for key, value in flat_map.items():
        translated_map[key] = translations.get(value, value)
        if translated_map[key] != value:
            print(f"   '{value}' → '{translated_map[key]}'")
    
    # Inject
    inject_response = requests.post(
        f"{BASE_URL}/inject",
        json={
            "flat_map": translated_map,
            "metadata": extract_data["metadata"],
            "format": "json"
        }
    )
    
    result = inject_response.json()
    print("\n3. Translated JSON:")
    print(result["content"])


def example_content_moderation():
    """Example of content moderation/filtering"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Content Moderation")
    print("=" * 60)
    
    json_content = {
        "comments": [
            {
                "user": "user1",
                "text": "This is a great product!"
            },
            {
                "user": "user2",
                "text": "Amazing quality and fast shipping"
            },
            {
                "user": "user3",
                "text": "Best purchase ever"
            }
        ]
    }
    
    json_string = json.dumps(json_content, indent=2)
    
    print("\n1. Original comments:")
    print(json_string)
    
    # Extract
    extract_response = requests.post(
        f"{BASE_URL}/extract",
        json={"content": json_string, "format": "json"}
    )
    
    extract_data = extract_response.json()
    flat_map = extract_data["flat_map"]
    
    # Moderate content (add sentiment tags)
    print("\n2. Adding sentiment analysis tags...")
    moderated_map = {}
    for key, value in flat_map.items():
        if any(word in value.lower() for word in ["great", "amazing", "best"]):
            moderated_map[key] = f"[POSITIVE] {value}"
            print(f"   Tagged as positive: {value}")
        else:
            moderated_map[key] = value
    
    # Inject
    inject_response = requests.post(
        f"{BASE_URL}/inject",
        json={
            "flat_map": moderated_map,
            "metadata": extract_data["metadata"],
            "format": "json"
        }
    )
    
    result = inject_response.json()
    print("\n3. Moderated JSON:")
    print(result["content"])


def example_data_anonymization():
    """Example of anonymizing personal data"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Data Anonymization")
    print("=" * 60)
    
    json_content = {
        "customer": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567"
        },
        "order": {
            "id": 12345,
            "items": ["Laptop", "Mouse"]
        }
    }
    
    json_string = json.dumps(json_content, indent=2)
    
    print("\n1. Original data with PII:")
    print(json_string)
    
    # Extract
    extract_response = requests.post(
        f"{BASE_URL}/extract",
        json={"content": json_string, "format": "json"}
    )
    
    extract_data = extract_response.json()
    flat_map = extract_data["flat_map"]
    
    # Anonymize
    print("\n2. Anonymizing personal information...")
    anonymized_map = {}
    for key, value in flat_map.items():
        if "@" in value:
            anonymized_map[key] = "***@***.com"
            print(f"   Email anonymized: {value} → {anonymized_map[key]}")
        elif "+" in value and "-" in value:
            anonymized_map[key] = "+X-XXX-XXX-XXXX"
            print(f"   Phone anonymized: {value} → {anonymized_map[key]}")
        elif value == "John Doe":
            anonymized_map[key] = "[REDACTED]"
            print(f"   Name anonymized: {value} → {anonymized_map[key]}")
        else:
            anonymized_map[key] = value
    
    # Inject
    inject_response = requests.post(
        f"{BASE_URL}/inject",
        json={
            "flat_map": anonymized_map,
            "metadata": extract_data["metadata"],
            "format": "json"
        }
    )
    
    result = inject_response.json()
    print("\n3. Anonymized JSON:")
    print(result["content"])


def main():
    """Run all examples"""
    print("\n" + "🔒 StructGuard-API Examples - JSON" + "\n")
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
        example_basic_json()
        example_multilingual_content()
        example_content_moderation()
        example_data_anonymization()
        
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
