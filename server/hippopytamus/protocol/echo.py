from hippopytamus.protocol.interface import Protocol, Servlet, Response, Request
from typing import Tuple, Dict


class EchoProtocol(Protocol):
    def feed_parse(self, buffer: bytes, _: Dict) -> Tuple[bytes, bool]:
        return buffer, True

    def parse_request(self, request: bytes, context: Dict) -> Response:
        return request

    def prepare_response(self, response: Response) -> bytes:
        if not isinstance(response, bytes):
            raise Exception("Error")
        return response


class EchoService(Servlet):
    def process_request(self, request: Request) -> Response:
        return request
