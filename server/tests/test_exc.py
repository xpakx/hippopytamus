import pytest
import threading
from hippopytamus.core.app import HippoApp, ServerOptions
from .utils import TestClient, get_free_port


@pytest.fixture
def app_server() -> int:
    port = get_free_port()
    app = HippoApp("hippopytamus.example.example3", ServerOptions(port=port, host="localhost"))
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


def test_response_status_annotation_on_exception(client: TestClient):
    resp = client.get("/exception")

    assert resp.code == 404
    assert resp.body == ''


def test_server_works_after_exception(client: TestClient):
    client.get("/exception")

    resp = client.get("/exception")

    assert resp.code == 404
