from http import HTTPStatus
from unittest import mock

import pytest
from requests.exceptions import RequestException
from requests.models import Response

from yfiles.yd_files.utils.timeout_requests import TimeoutRequest


@pytest.fixture
def timeout_request():
    """Fixture to create a TimeoutRequest instance."""
    return TimeoutRequest(total_timeout=2)  # 2 seconds for testing purposes


def test_initialization(timeout_request):
    """Test that TimeoutRequest initializes correctly."""
    test_delay = 2
    assert timeout_request.total_timeout == test_delay
    assert not timeout_request.timed_out
    assert not timeout_request.timeout_event.is_set()


@mock.patch("requests.get")
def test_get_request_within_timeout(mock_get, timeout_request):
    """Test successful GET request within the timeout."""
    mock_response = mock.Mock(spec=Response)
    mock_response.status_code = HTTPStatus.OK
    mock_get.return_value = mock_response

    response = timeout_request.get("http://example.com")

    assert response is not None
    assert response.status_code == HTTPStatus.OK
    assert timeout_request.timeout_event.is_set()
    assert not timeout_request.timed_out


@mock.patch("requests.get")
def test_request_exceeds_timeout(mock_get, timeout_request):
    """Test that a request exceeding timeout raises TimeoutError."""

    # Mock requests.get to simulate a delay
    def delayed_get(*args, **kwargs):
        import time

        time.sleep(3)  # Exceeds the timeout set below
        return mock.Mock(spec=Response)

    mock_get.side_effect = delayed_get

    # Set a short timeout for the test
    timeout_request.total_timeout = 1

    # Check if TimeoutError is raised in the context of pytest.raises
    with pytest.raises(TimeoutError, match="Request exceeded total timeout"):
        timeout_request.get("http://example.com")


@mock.patch("requests.get", side_effect=RequestException("Connection error"))
def test_get_request_exception_handling(mock_get, timeout_request):
    """Test that a request exception is handled gracefully."""
    response = timeout_request.get("http://example.com")
    assert response is None
    assert not timeout_request.timed_out
