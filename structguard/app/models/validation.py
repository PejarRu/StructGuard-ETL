from typing import List, Optional

from pydantic import BaseModel


class ChangeItem(BaseModel):
    """Represents a single text change in the validation report."""
    id: str
    context: str
    original_text: str
    new_text: str


class ValidationError(BaseModel):
    """Represents a validation error."""
    error: str
    message: Optional[str] = None
    id: Optional[str] = None
    item: Optional[dict] = None


class DiffStats(BaseModel):
    """Statistics about the diff between skeleton and modifications."""
    total_items: int
    modified_items: int
    unchanged_items: int
    modifications_provided: int
    missing_modifications: int
    unknown_ids: int


class ValidationReport(BaseModel):
    """Complete validation report."""
    status: str  # "valid" or "error"
    diff_stats: DiffStats
    changes: List[ChangeItem]
    errors: List[ValidationError]
