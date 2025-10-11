from abc import ABC, abstractmethod
from typing import Tuple, Dict
from hippopytamus.protocol.interface import Request


class HippoFilter(ABC):
    @abstractmethod
    def filter(self, request: Request, context: Dict) -> Tuple[bytes, bool]:
        """Filters requests"""
        pass
