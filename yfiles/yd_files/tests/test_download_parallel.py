from unittest import mock

from yfiles.yd_files.utils.download_parallel import download_parallel
from yfiles.yd_files.utils.obtain_fresh_download_url import (
    obtain_fresh_file_download_url,
)


# Define the mock function for TimeoutRequest.get
def mock_timeout_request_get(url, params=None, timeout=None, **kwargs):
    class MockResponse:
        def __init__(self, status_code, href=None):
            self.status_code = status_code
            self.elapsed = mock.Mock(total_seconds=mock.Mock(return_value=0.3))
            self._href = href

        def json(self):
            return {"href": self._href}

    # Simulate different responses based on file path in params
    if params["path"] == "/file1" or params["path"] == "/file3":
        return MockResponse(200, f"https://download_link/{params['path']}")
    return MockResponse(404)


# Use the mock function within the test
@mock.patch(
    "yfiles.yd_files.utils.timeout_requests.TimeoutRequest.get",
    side_effect=mock_timeout_request_get,
)
def test_download_parallel(mock_get):
    # Items to process, based on (public_link, path, file_id)
    items = [
        ("public_link_1", "/file1", 1),  # Should succeed
        ("public_link_2", "/file2", 2),  # Should fail with 404
        ("public_link_3", "/file3", 3),  # Should succeed
        ("public_link_4", "/file4", 4),  # Should fail with 404
    ]

    # Call download_parallel with obtain_fresh_file_download_url
    results = download_parallel(obtain_fresh_file_download_url, items)

    # Expected results based on the mock behavior
    expected_results = [
        ("https://download_link//file1", 0.3, 1),
        ("/file2", "public_link_2/file2 download failed with status code 404", 2),
        ("https://download_link//file3", 0.3, 3),
        ("/file4", "public_link_4/file4 download failed with status code 404", 4),
    ]

    # Sort results and expected results by file_id
    sorted_results = sorted(
        results,
        key=lambda x: x[2],
    )  # Sort by file_id (the third element in each tuple)
    sorted_expected = sorted(expected_results, key=lambda x: x[2])

    assert (
        sorted_results == sorted_expected
    ), f"Expected {sorted_expected}, but got {sorted_results}"
