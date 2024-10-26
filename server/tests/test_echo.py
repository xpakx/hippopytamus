import pytest
from hippopytamus.protocol.echo import EchoProtocol, EchoService


@pytest.fixture
def echo_protocol():
    return EchoProtocol()


@pytest.fixture
def echo_service():
    return EchoService()


def test_feed_parse(echo_protocol):
    buffer = b"example request"
    remaining_data, complete = echo_protocol.feed_parse(buffer, {})

    assert remaining_data == buffer
    assert complete is True


def test_parse_request(echo_protocol):
    request = b"example request"
    context = {}

    parsed_request = echo_protocol.parse_request(request, context)

    assert parsed_request == request


def test_prepare_response(echo_protocol):
    response = b"example response"

    prepared_response = echo_protocol.prepare_response(response)

    assert prepared_response == response


def test_process_request(echo_service):
    request = b"example request"

    processed_response = echo_service.process_request(request)

    assert processed_response == request
