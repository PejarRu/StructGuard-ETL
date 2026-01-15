from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    @abstractmethod
    def extract(self, source: bytes) -> Any:
        """Extract text segments from the provided source payload."""
        raise NotImplementedError

    @abstractmethod
    def inject(self, skeleton: bytes, modifications: bytes) -> Any:
        """Inject modified text segments back into the provided skeleton payload."""
        raise NotImplementedError

    @abstractmethod
    def validate(self, skeleton: bytes, modifications: bytes) -> dict:
        """
        Validate modifications against skeleton structure.
        
        Returns a dictionary with:
        - status: "valid" or "error"
        - diff_stats: Statistics about changes
        - changes: List of actual changes
        - errors: List of validation errors (if any)
        """
        raise NotImplementedError
