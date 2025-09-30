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
    client = TestClient()
    client.connect("localhost", app_server)
    msg = 'hello world'
    body = {'message': msg}

    resp = client.post("/h2/echo", body)
    client.close()

    assert "200" in resp.status
    assert f"You said: {msg}" in resp.body


@pytest.mark.parametrize(
    "msg",
    ["hello", "testing 123", ""]
)
def test_echo_str(app_server: int, msg):
    client = TestClient()
    client.connect("localhost", app_server)

    resp = client.post("/h2/echostr", msg)
    client.close()

    assert "200" in resp.status
    assert f"You said: {msg}" in resp.body
