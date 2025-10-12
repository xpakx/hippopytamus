from abc import ABC, abstractmethod
from typing import Dict
from hippopytamus.protocol.interface import Request


class HippoFilter(ABC):
    @abstractmethod
    def filter(self, request: Request, context: Dict) -> bool:
        """Filters requests"""
        pass
