import socket
import json
import time
from dataclasses import dataclass


@dataclass
class HttpResponse:
    method: str
    status: str
    headers: dict
    body: str


class TestClient:
    def connect(self, host: str, port: int) -> None:
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(2)
        time.sleep(0.5)  # TODO
        self.client.connect((host, port))

    def close(self) -> None:
        self.client.close()

    def send(self, method: str, uri: str, body=None, headers=None):
        self.client.sendall(make_request_bytes(method, uri, body=body, headers=headers))
        status, headers, resp_body = parse_http_response(self.client.recv(8192))
        return HttpResponse(
                method=method,
                status=status,
                headers=headers,
                body=resp_body,
        )

    def get(self, uri: str, headers=None):
        return self.send("GET", uri, headers=headers)

    def post(self, uri: str, body=None, headers=None):
        return self.send("POST", uri, body=body, headers=headers)


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", 0))
        return s.getsockname()[1]


def make_request_bytes(method: str, uri: str, headers=None, body=None) -> bytes:
    headers = headers or {}
    lines = [f"{method} {uri} HTTP/1.0"]
    lines.append("Host: localhost")

    body_bytes = b""
    if body is not None:
        print(type(body), body)
        if type(body) is dict:
            body_bytes = json.dumps(body).encode("utf-8")
        else:
            body_bytes = body.encode("utf-8")
        headers["Content-Length"] = str(len(body_bytes))
        body_bytes = body_bytes

    for key, value in headers.items():
        lines.append(f"{key}: {value}")

    lines.append("")
    header_bytes = "\r\n".join(lines).encode("utf-8")
    header_bytes = header_bytes + b"\r\n"

    return header_bytes + body_bytes


def parse_http_response(response_bytes: bytes):
    response_str = response_bytes.decode("utf-8")
    header_part, _, body = response_str.partition("\r\n\r\n")
    lines = header_part.split("\r\n")
    status_line = lines[0]
    headers = {}
    for line in lines[1:]:
        if ": " in line:
            key, value = line.split(": ", 1)
            headers[key] = value
    return status_line, headers, body

