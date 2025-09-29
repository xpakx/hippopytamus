import socket
import threading
import pytest
import json
from hippopytamus.core.app import HippoApp, ServerOptions
from typing import Generator
import time


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
        if type(body) is dict:
            body_bytes = json.dumps(body).encode("utf-8")
        else:
            body_bytes = body.encode("utf-8")
        headers["Content-Length"] = str(len(body_bytes))
        body_bytes = body_bytes + b'\r\n\r\n'

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


@pytest.fixture
def app_server() -> Generator[int, None, None]:
    port = get_free_port()
    app = HippoApp("hippopytamus.example", ServerOptions(port=port, host="localhost"))

    server_thread = threading.Thread(target=app.run, daemon=True)
    server_thread.start()

    yield port


@pytest.mark.parametrize("word", ["hello", "pyTest", "wow"])
def test_shout(app_server: int, word: str):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(2)
    time.sleep(0.5)  # TODO
    client.connect(("localhost", app_server))

    client.sendall(make_request_bytes("GET", f"/h2/shout/{word}"))
    status, headers, body = parse_http_response(client.recv(8192))
    client.close()

    assert "200" in status
    assert f"<h1>{word.upper()}!!!</h1>" in body


@pytest.mark.parametrize(
    "a,b,expected",
    [
        (2, 3, 5),
        (10, 0, 10),
        (7, None, 7),
    ]
)
def test_add_numbers(app_server: int, a, b, expected):
    query = f"/h2/add?a={a}"
    if b is not None:
        query += f"&b={b}"
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(2)
    time.sleep(0.5)  # TODO
    client.connect(("localhost", app_server))

    client.sendall(make_request_bytes("GET", query))
    status, headers, body = parse_http_response(client.recv(8192))
    client.close()

    assert "200" in status
    assert f"Sum = {expected}" in body


@pytest.mark.parametrize(
    "a,b,expected",
    [
        ("foo", "bar", "foobar"),
        ("x", None, "x0"),
    ]
)
def test_concat_numbers(app_server: int, a, b, expected):
    query = f"/h2/concat?a={a}"
    if b is not None:
        query += f"&b={b}"
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(2)
    time.sleep(0.5)  # TODO
    client.connect(("localhost", app_server))

    client.sendall(make_request_bytes("GET", query))
    status, headers, body = parse_http_response(client.recv(8192))
    client.close()

    assert "200" in status
    assert f"Sum = {expected}" in body
