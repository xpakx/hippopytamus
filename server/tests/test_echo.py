import pytest
from hippopytamus.protocol.echo import EchoProtocol, EchoService
from typing import Dict


@pytest.fixture
def echo_protocol() -> EchoProtocol:
    return EchoProtocol()


@pytest.fixture
def echo_service() -> EchoService:
    return EchoService()


def test_feed_parse(echo_protocol: EchoProtocol) -> None:
    buffer = b"example request"
    remaining_data, complete = echo_protocol.feed_parse(buffer, {})

    assert remaining_data == buffer
    assert complete is True


def test_parse_request(echo_protocol: EchoProtocol) -> None:
    request = b"example request"
    context: Dict = {}

    parsed_request = echo_protocol.parse_request(request, context)

    assert parsed_request == request


def test_prepare_response(echo_protocol: EchoProtocol) -> None:
    response = b"example response"

    prepared_response = echo_protocol.prepare_response(response)

    assert prepared_response == response


def test_process_request(echo_service: EchoService) -> None:
    request = b"example request"

    processed_response = echo_service.process_request(request)

    assert processed_response == request
