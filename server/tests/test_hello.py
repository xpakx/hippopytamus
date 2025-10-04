import threading
import pytest
from hippopytamus.core.app import HippoApp, ServerOptions
from typing import Generator
from .utils import get_free_port
from .utils import TestClient


@pytest.fixture
def app_server() -> Generator[int, None, None]:
    port = get_free_port()
    app = HippoApp("hippopytamus.example.example1", ServerOptions(port=port, host="localhost"))

    server_thread = threading.Thread(target=app.run, daemon=True)
    server_thread.start()

    yield port


@pytest.fixture
def client(app_server: int) -> Generator[TestClient, None, None]:
    client = TestClient()
    client.connect("localhost", app_server)
    try:
        yield client
    finally:
        client.close()


@pytest.mark.parametrize("word", ["hello", "pyTest", "wow"])
def test_shout(client: TestClient, word: str):
    resp = client.get(f"/h2/shout/{word}")

    assert resp.code == 200
    assert f"<h1>{word.upper()}!!!</h1>" in resp.body


@pytest.mark.parametrize(
    "a,b,expected",
    [
        (2, 3, 5),
        (10, 0, 10),
        (7, None, 7),
    ]
)
def test_add_numbers(client: TestClient, a, b, expected):
    query = f"/h2/add?a={a}"
    if b is not None:
        query += f"&b={b}"

    resp = client.get(query)

    assert resp.code == 200
    assert f"Sum = {expected}" in resp.body


@pytest.mark.parametrize(
    "a,b,expected",
    [
        ("foo", "bar", "foobar"),
        ("x", None, "x0"),
    ]
)
def test_concat_numbers(client: TestClient, a, b, expected):
    query = f"/h2/concat?a={a}"
    if b is not None:
        query += f"&b={b}"

    resp = client.get(query)

    assert resp.code == 200
    assert f"Sum = {expected}" in resp.body


def test_echo_body(client: TestClient):
    msg = 'hello world'
    body = {'message': msg}

    resp = client.post("/h2/echo", body)

    assert resp.code == 200
    assert f"You said: {msg}" in resp.body


@pytest.mark.parametrize(
    "msg",
    ["hello", "testing 123", ""]
)
def test_echo_str(client: TestClient, msg):
    resp = client.post("/h2/echostr", msg)

    assert resp.code == 200
    assert f"You said: {msg}" in resp.body
