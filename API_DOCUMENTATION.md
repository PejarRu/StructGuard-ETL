# StructGuard-API Documentation

## Overview

StructGuard-API is a stateless FastAPI middleware that acts as a "structural firewall" for Large Language Models (LLMs). It enables safe editing of massive XML/JSON documents by separating content from structure through an ETL (Extract-Transform-Load) workflow.

## Architecture

The API provides two main endpoints that work together:

1. **POST /extract** - Extracts editable text content into a flat map
2. **POST /inject** - Reconstructs the document with edited content

```
┌─────────────┐       ┌──────────┐       ┌─────────────┐
│ Original    │       │  Flat    │       │ Edited      │
│ XML/JSON    │──────>│  Map     │──────>│ XML/JSON    │
│             │ extract│ (Safe)   │inject │ (Structure  │
└─────────────┘       └──────────┘       │ Preserved)  │
                                          └─────────────┘
```

## API Endpoints

### Root Endpoint

**GET /**

Returns API information and available endpoints.

**Response:**
```json
{
  "name": "StructGuard-API",
  "description": "Structural firewall middleware for LLMs",
  "version": "1.0.0",
  "endpoints": {
    "/extract": "POST - Convert XML/JSON to flat map for safe editing",
    "/inject": "POST - Reconstruct file merging structure with edited texts"
  }
}
```

### Extract Endpoint

**POST /extract**

Extracts text content from XML or JSON into a flat map that can be safely edited without breaking the structure.

**Request Body:**
```json
{
  "content": "string (XML or JSON content)",
  "format": "string (either 'xml' or 'json')"
}
```

**Response:**
```json
{
  "flat_map": {
    "node_0": "extracted text 1",
    "node_1": "extracted text 2"
  },
  "metadata": {
    "original_content": "...",
    "node_info": [...],
    // Additional metadata for reconstruction
  }
}
```

**XML Example:**

Request:
```json
{
  "content": "<article><title>Hello</title><body>World</body></article>",
  "format": "xml"
}
```

Response:
```json
{
  "flat_map": {
    "node_0": "Hello",
    "node_1": "World"
  },
  "metadata": {
    "original_content": "<article><title>Hello</title><body>World</body></article>",
    "node_info": [
      {
        "key": "node_0",
        "path": "article/title",
        "type": "text",
        "tag": "title",
        "attrib": {}
      },
      {
        "key": "node_1",
        "path": "article/body",
        "type": "text",
        "tag": "body",
        "attrib": {}
      }
    ],
    "root_tag": "article",
    "root_attrib": {}
  }
}
```

**JSON Example:**

Request:
```json
{
  "content": "{\"name\": \"John\", \"skills\": [\"Python\", \"FastAPI\"]}",
  "format": "json"
}
```

Response:
```json
{
  "flat_map": {
    "node_0": "John",
    "node_1": "Python",
    "node_2": "FastAPI"
  },
  "metadata": {
    "original_content": "{\"name\": \"John\", \"skills\": [\"Python\", \"FastAPI\"]}",
    "paths": [
      {
        "key": "node_0",
        "path": "name",
        "value_type": "string"
      },
      {
        "key": "node_1",
        "path": "skills[0]",
        "value_type": "string"
      },
      {
        "key": "node_2",
        "path": "skills[1]",
        "value_type": "string"
      }
    ],
    "original_structure": {
      "name": "John",
      "skills": ["Python", "FastAPI"]
    }
  }
}
```

### Inject Endpoint

**POST /inject**

Reconstructs XML or JSON by merging the original structure with edited text content.

**Request Body:**
```json
{
  "flat_map": {
    "node_0": "edited text 1",
    "node_1": "edited text 2"
  },
  "metadata": {
    // Metadata from extract response
  },
  "format": "string (either 'xml' or 'json')"
}
```

**Response:**
```json
{
  "content": "reconstructed XML or JSON with edited content"
}
```

**Example:**

Request:
```json
{
  "flat_map": {
    "node_0": "Bonjour",
    "node_1": "Monde"
  },
  "metadata": {
    "original_content": "<article><title>Hello</title><body>World</body></article>",
    "node_info": [...]
  },
  "format": "xml"
}
```

Response:
```json
{
  "content": "<?xml version=\"1.0\" ?>\n<article>\n  <title>Bonjour</title>\n  <body>Monde</body>\n</article>"
}
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:

### 400 Bad Request

- Invalid XML/JSON syntax
- Unsupported format (must be 'xml' or 'json')

Example:
```json
{
  "detail": "Invalid XML: mismatched tag: line 1, column 18"
}
```

### 422 Validation Error

- Missing required fields
- Invalid data types

Example:
```json
{
  "detail": [
    {
      "loc": ["body", "format"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Use Cases

### 1. Content Translation

Extract text from multilingual documents, translate each text node, and inject back while preserving structure.

### 2. LLM Content Editing

Allow AI models to edit document content without breaking XML/JSON structure. The flat map prevents the AI from accidentally malforming tags or structure.

### 3. Content Sanitization

Extract text, apply sanitization/moderation, and reconstruct the document.

### 4. Bulk Text Processing

Apply transformations (uppercase, lowercase, etc.) to all text content while maintaining document structure.

### 5. Data Anonymization

Extract text, identify and redact PII (Personally Identifiable Information), and reconstruct.

## Best Practices

### 1. Preserve Metadata

Always store the `metadata` returned from the extract endpoint. It's required for reconstruction and contains structural information.

### 2. Handle All Nodes

When editing the flat map, ensure all keys from the original flat map are present in the edited version, even if unchanged.

### 3. Validate Before Inject

If possible, validate edited text before injection to ensure it doesn't contain problematic characters for the target format.

### 4. Error Handling

Implement proper error handling for both extract and inject operations. Check status codes and handle errors gracefully.

### 5. Batch Processing

For large documents, consider implementing timeouts and retry logic, as processing very large XML/JSON files may take time.

## Performance Considerations

- **Stateless Design**: Each request is independent, allowing horizontal scaling
- **Memory Efficient**: Uses streaming where possible for XML/JSON parsing
- **Fast Operations**: Typical extract/inject operations complete in milliseconds

## Limitations

1. **Text-Only**: Only string values are extracted. Numbers, booleans, and null values in JSON are preserved but not editable.
2. **Comments**: XML comments are not preserved during reconstruction.
3. **Processing Instructions**: XML processing instructions other than the declaration may not be preserved.
4. **Mixed Content**: XML mixed content (text and elements interleaved) is supported but may have edge cases.

## Security Considerations

1. **Input Validation**: Always validate input before sending to the API
2. **Size Limits**: Consider implementing request size limits for production deployments
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Content Sanitization**: Sanitize user-provided content before extraction

## Interactive API Documentation

When the server is running, access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive documentation where you can test the API directly from your browser.

## Code Examples

See the `examples/` directory for complete working examples:

- `examples/example_xml.py` - XML processing examples
- `examples/example_json.py` - JSON processing examples

## Support

For issues, questions, or contributions, please visit the GitHub repository.
