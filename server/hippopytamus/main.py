import socket
import os


host = '127.0.0.1'
port = 8000


class TCPServer:
    def __init__(self, protocol):
        self.protocol = protocol

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
            data = connection.recv(1024)  # TODO: protocol should decide
            result = self.protocol.process_request(data)
            connection.sendall(result)
            connection.close()


class EchoProtocol:
    def process_request(self, request: bytes):
        return request


class HttpProtocol09:
    def process_request(self, request: bytes):
        header, uri = self.parse_request(request)
        print(f"Method: {str(header)}")
        print(f"Resource: {str(uri)}")
        # TODO: should only parse request,
        # move constructing response to service
        if header != b"GET":
            return b"<h1>Unsupported!</h1>"
        if uri != b"/":
            return self.not_found()
        body, err = self.body_from_file("index.html")
        if err:
            return self.not_found()
        return body

    def parse_request(self, request: bytes) -> (str, str):
        lines = request.split(b"\r\n")
        header = lines[0].split(b" ")
        if len(header) < 2:
            return None
        method = header[0]
        uri = header[1]
        return method, uri

    def not_found(self) -> bytes:
        return b"<html><body><h1>No such file</h1></body></html>"

    def body_from_file(self, url: str) -> (bytes, str):
        if os.path.exists(url):
            with open(url, 'rb') as f:
                body = f.read()
            return body, None
        return None, "No such file"


if __name__ == "__main__":
    protocol = HttpProtocol09()
    server = TCPServer(protocol)
    server.listen()
