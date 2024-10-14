import socket
import os
from typing import Optional
from abc import ABC, abstractmethod

host = '127.0.0.1'
port = 8000


class Protocol(ABC):
    @abstractmethod
    def feed_parse(self, buffer: bytes, context: dict) -> (bytes, bool):
        """Prepares the response to be sent back."""
        pass

    @abstractmethod
    def parse_request(self, data: bytes, context: str):
        """Parses raw data into a request object."""
        pass

    @abstractmethod
    def prepare_response(self, response):
        """Prepares the response to be sent back."""
        pass


class TCPServer:
    def __init__(self, protocol: Protocol, service):
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
            read = False
            data = b''
            context = {}
            while not read:
                data += connection.recv(1024)
                data, read = protocol.feed_parse(data, context)
            request = self.protocol.parse_request(data, context)
            response = self.service.process_request(request)
            result = self.protocol.prepare_response(response)
            connection.sendall(result)
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
        return request


class HttpProtocol09(Protocol):
    def feed_parse(self, buffer, _):
        return buffer, True

    def prepare_response(self, resp: dict) -> bytes:
        return resp['body']

    def parse_request(self, request: bytes, context) -> Optional[dict]:
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


class HttpProtocol10(Protocol):
    codes = {200: b"OK", 501: b"Not Implemented", 404: b"Not Found"}

    def prepare_response(self, resp: dict) -> bytes:
        response = b"HTTP/1.0 "
        response += bytes(str(resp['code']), "ascii")
        response += b" "
        response += self.codes[resp['code']]
        response += b"\r\n"
        if 'headers' in resp:
            for key, value in resp['headers'].items():
                response += bytes(key, 'ascii')
                response += b': '
                response += bytes(value, 'ascii')
                response += b"\r\n"
        if resp['body']:
            response += b"\r\n"
            response += resp['body']
        return response

    def parse_headers(self, header: bytes) -> Optional[dict]:
        lines = header.split(b"\r\n")
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
        return {
                "method": method,
                "uri": uri,
                "version": version,
                "headers": headers
        }

    def parse_request(self, request: bytes, context: str) -> Optional[dict]:
        context = context['data']
        if 'headers' in context and 'Content-Length' in context['headers']:
            context['body'] = request.decode('utf-8')
        print(context)
        return context

    def feed_parse(self, buffer: bytes, context: dict) -> (bytes, bool):
        if 'headers_parsed' not in context:
            context['headers_parsed'] = False
            context['content_length'] = 0
            context['body'] = b""

        if not buffer:
            return buffer, True

        if not context['headers_parsed']:
            header_end_index = buffer.find(b"\r\n\r\n")
            if header_end_index != -1:
                headers, _, body = buffer.partition(b"\r\n\r\n")
                headers = self.parse_headers(headers)
                context['headers_parsed'] = True
                context['data'] = headers

                if 'headers' in headers and 'Content-Length' in headers['headers']:
                    context['content_length'] = int(headers['headers']['Content-Length'])
                buffer = body
            else:
                return (buffer, False)

        if context['headers_parsed']:
            fin = False
            if len(buffer) >= context['content_length']:
                fin = True
            return buffer, fin
        return buffer, False


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
        return {
                "code": 200,
                "body": body,
                "headers": {
                    "Server": "Hippopytamus",
                    "Content-Type": "text/html"
                }
        }

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
