from http import HTTPStatus
from unittest import mock

from requests.models import Response

from yfiles.yd_files.utils.obtain_fresh_download_url import (
    obtain_fresh_file_download_url,
)


# Function to simulate different responses from the `get` method
def mock_get(url, params=None, timeout=None):
    # Create a mock response object
    response = mock.Mock(spec=Response)

    # Set up the `elapsed` attribute with `total_seconds` as a mock method
    response.elapsed = mock.Mock()
    response.elapsed.total_seconds = mock.Mock(return_value=0.3)

    # Simulate a successful response
    if params["path"] == "/file1":
        response.status_code = HTTPStatus.OK
        response.json.return_value = {"href": "https://fresh.url/1"}
        return response

    # Simulate a failed response with a specific status code
    if params["path"] == "/file2":
        response.status_code = HTTPStatus.NOT_FOUND
        return response

    # Simulate a timeout by returning None or raising a Timeout exception
    if params["path"] == "/file3":
        return None  # Or raise `requests.exceptions.Timeout()`

    return None


@mock.patch(
    "yfiles.yd_files.utils.timeout_requests.TimeoutRequest.get",
    side_effect=mock_get,
)
def test_obtain_fresh_file_download_url(mock_get):
    # Test successful response
    result = obtain_fresh_file_download_url("public_link_1", "/file1", 1)
    assert result == ("https://fresh.url/1", 0.3, 1)

    # Test failed response (404 or any other error)
    result = obtain_fresh_file_download_url("public_link_2", "/file2", 2)
    assert result == (
        "/file2",
        "public_link_2/file2 download failed with status code 404",
        2,
    )

    # Test timeout (or no response)
    result = obtain_fresh_file_download_url("public_link_3", "/file3", 3)
    assert result == (
        "/file3",
        "public_link_3/file3 download failed with no response (likely a timeout)",
        3,
    )
