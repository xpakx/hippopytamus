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


class HttpProtocol10:
    codes = {200: b"OK", 501: b"Not Implemented", 404: b"Not Found"}

    def process_request(self, request: bytes):
        req = self.parse_request(request)
        print(f"Method: {req['method']}")
        print(f"Resource: {req['uri']}")
        # TODO: move to service
        if req['method'] != "GET":
            return self.response(code=501)
        if req['uri'] != "/":
            body, _ = self.body_from_file("404.html")
            return self.response(code=404, body=body)
        body, err = self.body_from_file("index.html")
        if err:
            body, _ = self.body_from_file("404.html")
            return self.response(code=404, body=body)
        return self.response(body=body)

    def response(self, code: int = 200, body: str = None):
        response = b"HTTP/1.0 "
        response += bytes(str(code), "ascii")
        response += b" "
        response += self.codes[code]
        response += b"\r\n"
        response += b"Server: Hippopytamus\r\n"
        if body:
            response += b"Content-Type: text/html\r\n"
            response += b"\r\n"
            response += body
        return response

    def parse_request(self, request: bytes):
        lines = request.split(b"\r\n")
        header = lines[0].split(b" ")
        if len(header) != 3:
            return None
        method = header[0].decode('utf-8')
        uri = header[1].decode('utf-8')
        version = header[2].decode('utf-8')
        request = {
                "method": method,
                "uri": uri,
                "version": version
        }
        return request

    def body_from_file(self, url: str) -> (bytes, str):
        if os.path.exists(url):
            with open(url, 'rb') as f:
                body = f.read()
            return body, None
        return None, "No such file"


if __name__ == "__main__":
    protocol = HttpProtocol10()
    server = TCPServer(protocol)
    server.listen()
