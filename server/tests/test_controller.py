import socket
import threading
import pytest
import json
from hippopytamus.core.app import HippoApp, ServerOptions
from typing import Generator


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
        body_str = json.dumps(body)
        body_bytes = body_str.encode("utf-8")
        headers["Content-Length"] = str(len(body_bytes))

    for key, value in headers.items():
        lines.append(f"{key}: {value}")

    lines.append("")
    header_bytes = "\r\n".join(lines).encode("utf-8")

    return header_bytes + body_bytes + b'\r\n'


@pytest.fixture
def app_server() -> Generator[int, None, None]:
    port = get_free_port()
    app = HippoApp("hippopytamus.example", ServerOptions(port=port, host="localhost"))

    server_thread = threading.Thread(target=app.run, daemon=True)
    server_thread.start()

    yield port


def test_hello_endpoint(app_server: int) -> None:
    print(app_server)

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(2)
    client.connect(("localhost", app_server))

    message = make_request_bytes(
        "GET",
        "/hello"
    )
    print(message)
    client.sendall(message)

    response_bytes = client.recv(4096)
    response = response_bytes.decode("utf-8")
    print(response)

    assert 'Hello world' in response

    client.close()
