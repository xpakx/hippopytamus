import os
from typing import Optional, Dict
from hippopytamus.protocol.interface import Protocol


class HttpProtocol09(Protocol):
    def feed_parse(self, buffer, _):
        return buffer, True

    def prepare_response(self, resp: Dict) -> bytes:
        return resp['body']

    def parse_request(self, request: bytes, context) -> Optional[Dict]:
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
