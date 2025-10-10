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


def test_response_reason_annotation_on_exception(client: TestClient):
    resp = client.get("/exception2")

    assert resp.code == 404
    assert resp.body == 'Test Not Found'


@pytest.mark.skip(reason="Not implemented")
def test_controller_exception_handler_without_body(client: TestClient):
    resp = client.get("/exception3")

    assert resp.code == 400
    assert resp.body == ''


@pytest.mark.skip(reason="Not implemented")
def test_controller_exception_handler_with_dict_return(client: TestClient):
    resp = client.get("/exception4")

    assert resp.code == 404
    assert resp.body == "Error 4"


@pytest.mark.skip(reason="Not implemented")
def test_global_exception_handler_from_advice(client: TestClient):
    resp = client.get("/exception5")

    assert resp.code == 400
    assert resp.body == "From Advice"


@pytest.mark.skip(reason="Not implemented")
def test_handlers_are_local(client: TestClient):
    resp = client.get("/another_exception")

    assert resp.code == 500
