import socket
import threading
import pytest
from hippopytamus.protocol.echo import EchoProtocol, EchoService
from hippopytamus.server.main import SimpleTCPServer
from typing import cast, Generator


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", 0))
        return cast(int, s.getsockname()[1])


@pytest.fixture
def server() -> Generator:
    port = get_free_port()
    protocol = EchoProtocol()
    service = EchoService()
    server = SimpleTCPServer(protocol, service, host="localhost", port=port)

    server_thread = threading.Thread(target=server.listen, daemon=True)
    server_thread.start()

    yield port


def test_echo_server(server: int) -> None:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("localhost", server))

    message = b"Hello, Server!"
    client_socket.sendall(message)

    response = client_socket.recv(1024)

    assert response == message

    client_socket.close()
