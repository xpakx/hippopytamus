import socket
import os
from typing import Optional


host = '127.0.0.1'
port = 8000


class TCPServer:
    def __init__(self, protocol, service):
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
            data = connection.recv(1024)  # TODO: protocol should decide
            request = self.protocol.parse_request(data)
            response = self.service.process_request(request)
            result = self.protocol.prepare_response(response)
            connection.sendall(result)
            connection.close()


class EchoProtocol:
    def parse_request(self, request: bytes) -> bytes:
        return request

    def prepare_response(self, response: bytes) -> bytes:
        return response


class EchoService():
    def process_request(self, request: bytes) -> bytes:
        return request


class HttpProtocol09:
    def prepare_response(self, resp: dict) -> bytes:
        return resp['body']

    def parse_request(self, request: bytes) -> Optional[dict]:
        lines = request.split(b"\r\n")
        header = lines[0].split(b" ")
        print(request)
        if len(header) < 2:
            return None
        method = header[0].decode('utf-8')
        uri = header[1].decode('utf-8')
        if method != "GET":
            return None
        return {
                "method": method,
                "uri": uri,
                "version": "0.9"
        }


class HttpProtocol10:
    codes = {200: b"OK", 501: b"Not Implemented", 404: b"Not Found"}

    def prepare_response(self, resp: dict) -> bytes:
        response = b"HTTP/1.0 "
        response += bytes(str(resp['code']), "ascii")
        response += b" "
        response += self.codes[resp['code']]
        response += b"\r\n"
        response += b"Server: Hippopytamus\r\n"
        if resp['body']:
            response += b"Content-Type: text/html\r\n"
            response += b"\r\n"
            response += resp['body']
        return response

    def parse_request(self, request: bytes) -> Optional[dict]:
        lines = request.split(b"\r\n")
        header = lines[0].split(b" ")
        if len(header) != 3:
            return None
        method = header[0].decode('utf-8')
        uri = header[1].decode('utf-8')
        version = header[2].decode('utf-8')

        headers = {}
        for line in lines[1:]:
            if line == b'':
                break
            headersplit = line.split(b":", 1)
            if len(headersplit) != 2:
                return None  # TODO: 400
            header_key = headersplit[0].decode('utf-8')
            header_value = headersplit[1].decode('utf-8').lstrip()
            headers[header_key] = header_value
        request = {
                "method": method,
                "uri": uri,
                "version": version,
                "headers": headers
        }
        print(request)
        return request


class HttpService():
    def process_request(self, request: dict) -> dict:
        print(f"Method: {request['method']}")
        print(f"Resource: {request['uri']}")
        if request['method'] != "GET":
            return {"code": 501, "body": ""}
        if request['uri'] != "/":
            body, _ = self.body_from_file("404.html")
            return {"code": 404, "body": body}
        body, err = self.body_from_file("index.html")
        if err:
            body, _ = self.body_from_file("404.html")
            return {"code": 404, "body": body}
        return {"code": 200, "body": body}

    def body_from_file(self, url: str) -> (bytes, str):
        if os.path.exists(url):
            with open(url, 'rb') as f:
                body = f.read()
            return body, None
        return None, "No such file"


if __name__ == "__main__":
    protocol = HttpProtocol10()
    service = HttpService()
    server = TCPServer(protocol, service)
    server.listen()
