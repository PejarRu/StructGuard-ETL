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
