from fastapi import APIRouter, File, UploadFile
from fastapi.responses import Response

from app.adapters.wordpress_xml import WordPressXmlAdapter

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
    - skeleton_file: The original XML file (with sg-id attributes from extraction)
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
