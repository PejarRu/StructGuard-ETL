from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse, Response

from app.adapters.wordpress_xml import WordPressXmlAdapter
from app.models.validation import ValidationReport

router = APIRouter(prefix="/v1", tags=["etl"])


@router.post("/extract")
async def extract(file: UploadFile = File(...)):
    """
    Receive an XML/JSON file and return extracted text segments.
    
    Returns JSON with extraction schema containing:
    - id: unique identifier for each segment
    - context: contextual information about the segment
    - original_text: the original text content
    - edited_text: null (to be filled by AI/editor)
    """
    content = await file.read()
    
    # For now, we assume WordPress XML format
    # Future: detect format and select appropriate adapter
    adapter = WordPressXmlAdapter()
    
    result = adapter.extract(content)
    
    return Response(
        content=result,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="extraction_{file.filename}.json"'
        },
    )


@router.post("/inject")
async def inject(
    skeleton_file: UploadFile = File(...),
    modifications_file: UploadFile = File(...),
):
    """
    Receive the skeleton file plus modifications and return reconstructed output.
    
    Input:
    - skeleton_file: The original XML file (clean, without sg-id attributes)
    - modifications_file: JSON file with edited_text populated
    
    Output: Reconstructed XML file with modifications applied
    """
    skeleton_content = await skeleton_file.read()
    modifications_content = await modifications_file.read()
    
    # For now, we assume WordPress XML format
    adapter = WordPressXmlAdapter()
    
    result = adapter.inject(skeleton_content, modifications_content)
    
    return Response(
        content=result,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="modified_{skeleton_file.filename}"'
        },
    )


@router.post("/validate", response_model=ValidationReport)
async def validate(
    skeleton_file: UploadFile = File(...),
    modifications_file: UploadFile = File(...),
):
    """
    Validate modifications against skeleton structure and return diff report.
    
    Input:
    - skeleton_file: The original XML file
    - modifications_file: JSON file with edited_text populated
    
    Output: JSON validation report containing:
    - status: "valid" or "error"
    - diff_stats: Statistics about total items, changes, errors
    - changes: List of items where text was actually modified
    - errors: List of validation errors (missing IDs, unknown IDs, etc.)
    """
    skeleton_content = await skeleton_file.read()
    modifications_content = await modifications_file.read()
    
    # For now, we assume WordPress XML format
    adapter = WordPressXmlAdapter()
    
    validation_result = adapter.validate(skeleton_content, modifications_content)
    
    return JSONResponse(content=validation_result)
