import pytest
import threading
from hippopytamus.core.app import HippoApp, ServerOptions
from .utils import TestClient, get_free_port


@pytest.fixture
def app_server() -> int:
    port = get_free_port()
    app = HippoApp("hippopytamus.example.example2", ServerOptions(port=port, host="localhost"))
    thread = threading.Thread(target=app.run, daemon=True)
    thread.start()
    return port


@pytest.fixture
def client(app_server: int) -> TestClient:
    c = TestClient()
    c.connect("localhost", app_server)
    try:
        yield c
    finally:
        c.close()


def test_hello_triggers_exception_handler(client: TestClient):
    resp = client.get("/hello")

    assert resp.code == 500
    assert "Test error" in resp.body


def test_server_works_after_exception(client: TestClient):
    client.get("/hello")

    resp = client.get("/hello")

    assert resp.code == 500
    assert "Test error" in resp.body
