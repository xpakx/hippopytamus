from abc import ABC, abstractmethod
from typing import Tuple, Dict, Union, Any

Response = Union[bytes, None, Dict[str, Any], str]
Request = Union[bytes, None, Dict[str, Any], str]


class Protocol(ABC):
    @abstractmethod
    def feed_parse(self, buffer: bytes, context: Dict) -> Tuple[bytes, bool]:
        """Prepares the response to be sent back."""
        pass

    @abstractmethod
    def parse_request(self, data: bytes, context: Dict) -> Response:
        """Parses raw data into a request object."""
        pass

    @abstractmethod
    def prepare_response(self, response: Response) -> bytes:
        """Prepares the response to be sent back."""
        pass


class Servlet(ABC):
    @abstractmethod
    def process_request(self, request: Request) -> Response:
        """Process the request and generates a response."""
        pass
