import pytest
import threading
from hippopytamus.core.app import HippoApp, ServerOptions
from .utils import TestClient, get_free_port


@pytest.fixture
def app_server() -> int:
    port = get_free_port()
    app = HippoApp("hippopytamus.example", ServerOptions(port=port, host="localhost"))
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


def test_api_test(client: TestClient):
    resp = client.get("/api/test")

    assert "200" in resp.status
    assert "<h1>Dependency test</h1>" in resp.body


@pytest.mark.skip(reason="Auto-json transformation of response not implemented yet")
def test_path_variable(client: TestClient):
    user_id = 7
    resp = client.get(f"/api/hello/{user_id}")

    assert "200" in resp.status
    assert f"User#{user_id}" in resp.body


@pytest.mark.parametrize("user_id", [1, 99, 123])
@pytest.mark.skip(reason="Auto-json transformation of response not implemented yet")
def test_var_route_handling(client: TestClient, user_id: int):
    request_id = f"req-{user_id}"
    resp = client.get(f"/api/hello/{user_id}")

    assert "200" in resp.status
    assert f"User#{user_id}" in resp.body
    assert request_id in resp.body


@pytest.mark.skip(reason="Headers not implemented yet")
def test_hello_with_headers(client: TestClient):
    user_id = 10
    headers = {"X-Request-ID": "header-123"}
    resp = client.get(f"/api/hello/{user_id}", headers=headers)

    assert "200" in resp.status
    assert "User#10" in resp.body
    assert "header-123" in resp.body
