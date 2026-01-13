# Project: StructGuard-API

## 1. Project Manifesto
StructGuard-API is a high-integrity, stateless middleware designed to act as a Structural Firewall between structured data files (XML, JSON) and Large Language Models (LLMs).

The Core Problem: LLMs often hallucinate or corrupt file syntax (tags, attributes, nesting) when editing large files.
The Solution: A native Python extraction-injection pipeline that strictly isolates content from structure. The AI never sees the tags, only the text.

## 2. Architectural Principles

### A. Statelessness (Zero-Storage Policy)
* The API MUST NOT rely on a database or server-side file storage to persist state between requests.
* Mechanism: The state (the original file structure) is held by the client and re-uploaded during the injection phase.

### B. The Adapter Pattern
* The system must use a modular Adapter design.
* BaseAdapter: Abstract class defining extract() and inject().
* WordPressXmlAdapter: Implementation using lxml for .xml files (critical for CDATA and namespaces).
* JsonAdapter: (Future) Implementation for .json localization files.

## 3. Data Workflow & API Endpoints

### Endpoint 1: /v1/extract (The Lock)
* Method: POST
* Input: multipart/form-data -> file (The source XML).
* Logic:
    1. Identify the Adapter.
    2. Parse the file into a DOM/Tree using lxml.
    3. Traverse the DOM finding Safe Zones (content:encoded, title, excerpt, and ACF wp:meta_value).
    4. Generate a unique ID for each segment.
* Output: A JSON file containing the Extraction Schema:
    [ { "id": "uuid_or_xpath", "context": "Title: ...", "original_text": "...", "edited_text": null } ]

### Endpoint 2: /v1/inject (The Reconstruction)
* Method: POST
* Input: multipart/form-data
    1. skeleton_file: The Original source file (re-uploaded by the client).
    2. modifications_file: The JSON file returned by the AI.
* Logic:
    1. Parse skeleton_file into a DOM using lxml.
    2. Load modifications_file into a Map.
    3. Iterate through the Map. For each ID, locate the node in the DOM and swap the text content.
    4. Sanitization: If the original node used CDATA, the new content MUST be wrapped in CDATA.
    5. Serialize the DOM back to a file string.
* Output: File stream (attachment) with the reconstructed document.

## 4. Technical Constraints & Stack

### Core Technologies
* Language: Python 3.11+
* Framework: FastAPI.
* Server: Uvicorn.

### Critical Libraries
* XML Handling: lxml (Strict Requirement). Must be used for all XML parsing to ensure CDATA preservation. Standard xml.etree is forbidden.
* Validation: pydantic.

## 5. Folder Structure
/structguard
  /app
    /adapters       # Logic for parsing XML/JSON
       base.py
       wordpress_xml.py
    /core           # Config
    /models         # Pydantic Schemas
    /routers        # FastAPI Routes
    main.py         # Entry point
  Dockerfile
  requirements.txt
  tests/

## 6. Definition of Done
The project is functional when:
1. XML Upload (/extract) returns a valid JSON.
2. XML + Modified JSON Upload (/inject) returns a valid XML.
3. The output XML is structurally identical to the original (same tags, attributes, CDATA) with only text values changed.