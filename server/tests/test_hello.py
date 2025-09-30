import socket
import threading
import pytest
from hippopytamus.core.app import HippoApp, ServerOptions
from typing import Generator
import time
from .utils import get_free_port, make_request_bytes, parse_http_response
from .utils import TestClient


@pytest.fixture
def app_server() -> Generator[int, None, None]:
    port = get_free_port()
    app = HippoApp("hippopytamus.example", ServerOptions(port=port, host="localhost"))

    server_thread = threading.Thread(target=app.run, daemon=True)
    server_thread.start()

    yield port


@pytest.mark.parametrize("word", ["hello", "pyTest", "wow"])
def test_shout(app_server: int, word: str):
    client = TestClient()
    client.connect("localhost", app_server)

    resp = client.get(f"/h2/shout/{word}")
    client.close()

    assert "200" in resp.status
    assert f"<h1>{word.upper()}!!!</h1>" in resp.body


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
    client = TestClient()
    client.connect("localhost", app_server)

    resp = client.get(query)
    client.close()

    assert "200" in resp.status
    assert f"Sum = {expected}" in resp.body


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
    client = TestClient()
    client.connect("localhost", app_server)

    resp = client.get(query)
    client.close()

    assert "200" in resp.status
    assert f"Sum = {expected}" in resp.body


def test_echo_body(app_server: int):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(2)
    time.sleep(0.5)  # TODO
    client.connect(("localhost", app_server))
    msg = 'hello world'
    body = {'message': msg}

    client.sendall(make_request_bytes("POST", "/h2/echo", body=body))
    status, headers, body_resp = parse_http_response(client.recv(8192))
    client.close()

    assert "200" in status
    assert f"You said: {msg}" in body_resp


@pytest.mark.parametrize(
    "msg",
    ["hello", "testing 123", ""]
)
def test_echo_str(app_server: int, msg):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(2)
    time.sleep(0.5)  # TODO
    client.connect(("localhost", app_server))

    client.sendall(make_request_bytes("POST", "/h2/echostr", body=msg))
    status, headers, body_resp = parse_http_response(client.recv(8192))
    client.close()

    assert "200" in status
    assert f"You said: {msg}" in body_resp
