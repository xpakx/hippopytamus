from hippopytamus.protocol.interface import Protocol


class EchoProtocol(Protocol):
    def feed_parse(self, buffer, _):
        return buffer, True

    def parse_request(self, request: bytes, context) -> bytes:
        return request

    def prepare_response(self, response: bytes) -> bytes:
        return response


class EchoService():
    def process_request(self, request: bytes) -> bytes:
        return request
