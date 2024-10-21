import socket
from typing import Optional
from hippopytamus.protocol.http import HttpProtocol10, HttpService
from hippopytamus.protocol.interface import Protocol, Servlet

host = '127.0.0.1'
port = 8000


class TCPServer:
    def __init__(self, protocol: Protocol, service: Servlet):
        self.protocol = protocol
        self.service = service

    def listen(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # TODO: timeout (maybe?)
        sock.bind((host, port))

        sock.listen()
        print(sock.getsockname())

        while True:
            connection, address = sock.accept()

            print(f"new client: {address}")
            context = {}
            while True:
                read = False
                data = b''
                while not read:
                    data += connection.recv(1024)
                    data, read = self.protocol.feed_parse(data, context)
                request = self.protocol.parse_request(data, context)
                response = self.service.process_request(request)
                result = self.protocol.prepare_response(response)
                connection.sendall(result)
                if 'keep-alive' not in context:
                    break
            connection.close()


class EchoProtocol(Protocol):
    def feed_parse(self, buffer, _):
        return buffer, True

    def parse_request(self, request: bytes, context) -> bytes:
        return request

    def prepare_response(self, response: bytes) -> bytes:
        return response


class EchoService():
    def process_request(self, request: bytes) -> bytes:
        print(request)
        return request


if __name__ == "__main__":
    protocol = HttpProtocol10()
    service = HttpService()
    server = TCPServer(protocol, service)
    server.listen()
