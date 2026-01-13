"""
StructGuard-API: Stateless FastAPI middleware for structure-preserving content transformation.
Acts as a structural firewall for LLMs to edit massive texts without breaking XML/JSON structure.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

app = FastAPI(
    title="StructGuard-API",
    description="Structural firewall middleware for LLMs - ETL for safe content editing",
    version="1.0.0"
)


class ExtractRequest(BaseModel):
    """Request model for the extract endpoint"""
    content: str = Field(..., description="XML or JSON content to extract")
    format: str = Field(..., description="Format type: 'xml' or 'json'")


class ExtractResponse(BaseModel):
    """Response model for the extract endpoint"""
    flat_map: Dict[str, str] = Field(..., description="Flat map of extracted text content")
    metadata: Dict[str, Any] = Field(..., description="Metadata for reconstruction")


class InjectRequest(BaseModel):
    """Request model for the inject endpoint"""
    flat_map: Dict[str, str] = Field(..., description="Edited flat map of text content")
    metadata: Dict[str, Any] = Field(..., description="Metadata from extract operation")
    format: str = Field(..., description="Format type: 'xml' or 'json'")


class InjectResponse(BaseModel):
    """Response model for the inject endpoint"""
    content: str = Field(..., description="Reconstructed XML or JSON with edited content")


def extract_xml(xml_content: str) -> tuple[Dict[str, str], Dict[str, Any]]:
    """
    Extract text content from XML into a flat map.
    
    Args:
        xml_content: XML string to extract from
        
    Returns:
        tuple: (flat_map, metadata) where flat_map contains editable texts
               and metadata contains structure information
    """
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise HTTPException(status_code=400, detail=f"Invalid XML: {str(e)}")
    
    flat_map = {}
    node_info = []
    counter = [0]  # Use list to allow modification in nested function
    
    def traverse(element, path=""):
        """Recursively traverse XML tree and extract text content"""
        current_path = f"{path}/{element.tag}" if path else element.tag
        
        # Extract element text
        if element.text and element.text.strip():
            key = f"node_{counter[0]}"
            flat_map[key] = element.text.strip()
            node_info.append({
                "key": key,
                "path": current_path,
                "type": "text",
                "tag": element.tag,
                "attrib": dict(element.attrib)
            })
            counter[0] += 1
        
        # Process children
        for child in element:
            traverse(child, current_path)
            
            # Extract tail text (text after child element)
            if child.tail and child.tail.strip():
                key = f"node_{counter[0]}"
                flat_map[key] = child.tail.strip()
                node_info.append({
                    "key": key,
                    "path": current_path,
                    "type": "tail",
                    "tag": child.tag,
                    "attrib": dict(child.attrib)
                })
                counter[0] += 1
    
    traverse(root)
    
    metadata = {
        "original_content": xml_content,
        "node_info": node_info,
        "root_tag": root.tag,
        "root_attrib": dict(root.attrib)
    }
    
    return flat_map, metadata


def extract_json(json_content: str) -> tuple[Dict[str, str], Dict[str, Any]]:
    """
    Extract text content from JSON into a flat map.
    
    Args:
        json_content: JSON string to extract from
        
    Returns:
        tuple: (flat_map, metadata) where flat_map contains editable texts
               and metadata contains structure information
    """
    try:
        data = json.loads(json_content)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    
    flat_map = {}
    paths = []
    counter = [0]
    
    def traverse(obj, path=""):
        """Recursively traverse JSON and extract string values"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                traverse(value, current_path)
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                current_path = f"{path}[{idx}]"
                traverse(item, current_path)
        elif isinstance(obj, str):
            key = f"node_{counter[0]}"
            flat_map[key] = obj
            paths.append({
                "key": key,
                "path": path,
                "value_type": "string"
            })
            counter[0] += 1
    
    traverse(data)
    
    metadata = {
        "original_content": json_content,
        "paths": paths,
        "original_structure": data
    }
    
    return flat_map, metadata


def inject_xml(flat_map: Dict[str, str], metadata: Dict[str, Any]) -> str:
    """
    Reconstruct XML by merging original structure with edited texts.
    
    Args:
        flat_map: Edited flat map of text content
        metadata: Metadata from extract operation
        
    Returns:
        str: Reconstructed XML string
    """
    try:
        root = ET.fromstring(metadata["original_content"])
    except ET.ParseError as e:
        raise HTTPException(status_code=400, detail=f"Invalid metadata XML: {str(e)}")
    
    # Build a mapping from path to elements
    node_map = {}
    
    def build_node_map(element, path=""):
        """Build a map of paths to elements"""
        current_path = f"{path}/{element.tag}" if path else element.tag
        if current_path not in node_map:
            node_map[current_path] = []
        node_map[current_path].append(element)
        
        for child in element:
            build_node_map(child, current_path)
    
    build_node_map(root)
    
    # Apply edited texts
    processed = set()
    for node_data in metadata["node_info"]:
        key = node_data["key"]
        if key not in flat_map:
            continue
            
        path = node_data["path"]
        node_type = node_data["type"]
        edited_text = flat_map[key]
        
        # Find matching element(s)
        if path in node_map:
            for element in node_map[path]:
                # Create unique identifier to avoid duplicate processing
                elem_id = (id(element), node_type, node_data.get("tag"))
                if elem_id in processed:
                    continue
                    
                if node_type == "text":
                    element.text = edited_text
                    processed.add(elem_id)
                    break
                elif node_type == "tail":
                    # Find child with matching tag for tail
                    for child in element:
                        if child.tag == node_data["tag"]:
                            child.tail = edited_text
                            processed.add(elem_id)
                            break
    
    # Convert back to string with pretty formatting
    xml_str = ET.tostring(root, encoding='unicode', method='xml')
    
    try:
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ").strip()
    except:
        # Fallback to non-pretty version if pretty print fails
        return xml_str


def inject_json(flat_map: Dict[str, str], metadata: Dict[str, Any]) -> str:
    """
    Reconstruct JSON by merging original structure with edited texts.
    
    Args:
        flat_map: Edited flat map of text content
        metadata: Metadata from extract operation
        
    Returns:
        str: Reconstructed JSON string
    """
    # Deep copy the original structure
    def deep_copy(obj):
        if isinstance(obj, dict):
            return {k: deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [deep_copy(item) for item in obj]
        else:
            return obj
    
    result = deep_copy(metadata["original_structure"])
    
    # Apply edited texts
    for path_data in metadata["paths"]:
        key = path_data["key"]
        if key not in flat_map:
            continue
            
        path = path_data["path"]
        edited_text = flat_map[key]
        
        # Parse path into parts (handle both dots and brackets)
        # Example: "document.chapters[0].paragraphs[1]" -> ["document", "chapters", 0, "paragraphs", 1]
        parts = []
        i = 0
        current_part = ""
        
        while i < len(path):
            char = path[i]
            if char == '.':
                if current_part:
                    parts.append(current_part)
                    current_part = ""
            elif char == '[':
                if current_part:
                    parts.append(current_part)
                    current_part = ""
                # Extract index
                j = i + 1
                while j < len(path) and path[j] != ']':
                    j += 1
                parts.append(int(path[i+1:j]))
                i = j  # Skip to closing bracket
            else:
                current_part += char
            i += 1
        
        # Add last part if any
        if current_part:
            parts.append(current_part)
        
        # Navigate to parent and update value
        if not parts:
            continue
            
        current_obj = result
        for i, part in enumerate(parts[:-1]):
            if isinstance(part, int):
                current_obj = current_obj[part]
            else:
                current_obj = current_obj[part]
        
        # Update the final value
        last_part = parts[-1]
        if isinstance(last_part, int):
            current_obj[last_part] = edited_text
        else:
            current_obj[last_part] = edited_text
    
    return json.dumps(result, indent=2, ensure_ascii=False)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "StructGuard-API",
        "description": "Structural firewall middleware for LLMs",
        "version": "1.0.0",
        "endpoints": {
            "/extract": "POST - Convert XML/JSON to flat map for safe editing",
            "/inject": "POST - Reconstruct file merging structure with edited texts"
        }
    }


@app.post("/extract", response_model=ExtractResponse)
async def extract(request: ExtractRequest):
    """
    Extract text content from XML or JSON into a flat map.
    
    This endpoint converts structured data (XML/JSON) into a flat map
    that can be safely edited without breaking the structure.
    
    Args:
        request: ExtractRequest with content and format
        
    Returns:
        ExtractResponse with flat_map and metadata
    """
    if request.format.lower() == "xml":
        flat_map, metadata = extract_xml(request.content)
    elif request.format.lower() == "json":
        flat_map, metadata = extract_json(request.content)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {request.format}. Use 'xml' or 'json'"
        )
    
    return ExtractResponse(flat_map=flat_map, metadata=metadata)


@app.post("/inject", response_model=InjectResponse)
async def inject(request: InjectRequest):
    """
    Reconstruct XML or JSON by merging original structure with edited texts.
    
    This endpoint takes the edited flat map and metadata from the extract
    operation and reconstructs the original structure with updated content.
    
    Args:
        request: InjectRequest with edited flat_map, metadata, and format
        
    Returns:
        InjectResponse with reconstructed content
    """
    if request.format.lower() == "xml":
        content = inject_xml(request.flat_map, request.metadata)
    elif request.format.lower() == "json":
        content = inject_json(request.flat_map, request.metadata)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {request.format}. Use 'xml' or 'json'"
        )
    
    return InjectResponse(content=content)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
