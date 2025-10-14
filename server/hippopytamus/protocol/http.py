import os
from typing import Optional, Dict, Tuple, cast
from hippopytamus.protocol.interface import Protocol, Servlet, Request, Response
from hippopytamus.logger.logger import LoggerFactory


class HttpProtocol09(Protocol):
    def __init__(self) -> None:
        self.logger = LoggerFactory.get_logger()

    def feed_parse(self, buffer: bytes, _: Dict) -> Tuple[bytes, bool]:
        return buffer, True

    def prepare_response(self, resp: Response) -> bytes:
        if not isinstance(resp, dict):
            raise Exception("Error")
        return cast(bytes, resp['body'])

    def parse_request(self, request: bytes, context: Dict) -> Optional[Dict]:
        lines = request.split(b"\r\n")
        header = lines[0].split(b" ")
        self.logger.debug(request)
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
    codes = {
            200: b"OK",
            400: b"Bad Request",
            403: b"Forbidden",
            404: b"Not Found",
            500: b"Internal Server Error",
            501: b"Not Implemented",
    }

    def __init__(self) -> None:
        self.logger = LoggerFactory.get_logger()

    def prepare_response(self, resp: Response) -> bytes:
        if not isinstance(resp, dict):
            raise Exception("Error")
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

    def parse_headers(self, header: bytes) -> Optional[Dict]:
        lines = header.split(b"\r\n")
        header_data = lines[0].split(b" ")
        if len(header_data) != 3:
            return None
        method = header_data[0].decode('utf-8')
        uri = header_data[1].decode('utf-8')
        version = header_data[2].decode('utf-8')

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

    def parse_request(self, request: bytes, context: Dict) -> Optional[Dict]:
        context = context['data']
        if 'headers' in context and 'Content-Length' in context['headers']:
            context['body'] = request.decode('utf-8')
        self.logger.debug(context)
        return context

    def feed_parse(self, buffer: bytes, context: dict) -> Tuple[bytes, bool]:
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
                headers_data = self.parse_headers(headers)
                if not headers_data:
                    return buffer, True
                context['headers_parsed'] = True
                context['data'] = headers_data

                if 'headers' in headers_data and 'Content-Length' in headers_data['headers']:
                    context['content_length'] = int(headers_data['headers']['Content-Length'])
                buffer = body
            else:
                return (buffer, False)

        if context['headers_parsed']:
            fin = False
            if len(buffer) >= context['content_length']:
                fin = True
            return buffer, fin
        return buffer, False


class HttpService(Servlet):
    def __init__(self) -> None:
        self.logger = LoggerFactory.get_logger()

    def process_request(self, request: Request) -> Response:
        if not isinstance(request, dict):
            raise Exception("Error")
        self.logger.debug(f"Method: {request['method']}")
        self.logger.debug(f"Resource: {request['uri']}")
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

    def body_from_file(self, url: str) -> Tuple[Optional[bytes], Optional[str]]:
        if os.path.exists(url):
            with open(url, 'rb') as f:
                body = f.read()
            return body, None
        return None, "No such file"
