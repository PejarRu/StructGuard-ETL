from typing import Optional

from pydantic import BaseModel


class ExtractionItem(BaseModel):
    id: str
    context: Optional[str] = None
    original_text: str
    edited_text: Optional[str] = None
