import threading
import pytest
from hippopytamus.core.app import HippoApp, ServerOptions
from typing import Generator
from .utils import get_free_port
from .utils import TestClient


@pytest.fixture
def app_server() -> Generator[int, None, None]:
    port = get_free_port()
    app = HippoApp("hippopytamus.example", ServerOptions(port=port, host="localhost"))

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


def test_hello_endpoint(client: TestClient) -> None:
    resp = client.get("/hello")

    assert "200" in resp.status
    assert "<h1>Hello world from service!</h1>" in resp.body


def test_hello_query_param(client: TestClient):
    resp = client.get("/hello?name=Alice")

    assert "200" in resp.status
    assert "<h1>Hello Alice from service!</h1>" in resp.body


def test_home_index(client: TestClient):
    resp = client.get("/")

    assert "200" in resp.status
    assert "<title>Hippopytamus</title>" in resp.body


def test_404_path(client: TestClient):
    resp = client.get("/unknown")

    assert "404" in resp.status
    assert "Not found" in resp.body
