import socket
from hippopytamus.protocol.interface import Protocol, Servlet
import threading
from typing import Dict, Any


class ThreadedTCPServer:
    def __init__(self, protocol: Protocol, service: Servlet,
                 host: str = "localhost", port: int = 8000) -> None:
        self.protocol = protocol
        self.service = service
        self.host = host
        self.port = port

    def listen(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))

        sock.listen()
        print(sock.getsockname())

        while True:
            connection, address = sock.accept()
            print(f"new client: {address}")
            client = threading.Thread(
                    target=self.thread,
                    args=(connection, address,)
            )
            client.start()

    def thread(self, connection: socket.socket, address: socket._RetAddress):
        context: Dict[str, Any] = {}
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
