import logging
import threading

import requests
from requests import Response

logger = logging.getLogger("yfiles")


class TimeoutRequest:
    """
    Manages HTTP requests with a custom total timeout across connection
    and read durations. Ensures that the request does not exceed the specified
    timeout period by raising a TimeoutError if the threshold is surpassed.

    Attributes:
        total_timeout (int): Maximum total timeout duration for the request in seconds.
        timeout_event (threading.Event): Event to signal when the request completes.
        timed_out (bool): Flag indicating whether a timeout occurred.

    Methods:
        get(url: str, **kwargs) -> Optional[Response]:
            Sends a GET request to the specified URL and returns the response if
            successful within the timeout period. Returns None otherwise.
    """

    def __init__(self, total_timeout: int):
        """
        Initializes TimeoutRequest with a specified timeout duration.

        Args:
            total_timeout (int): Maximum total timeout in seconds.
        """
        self.total_timeout = total_timeout
        self.timeout_event = threading.Event()
        self.timed_out = False

    def _timeout_handler(self):
        """
        Waits for the total timeout duration, and if exceeded, logs an error,
        sets the timeout flag, and raises a TimeoutError.
        """
        if not self.timeout_event.wait(
            self.total_timeout,
        ):
            self.timed_out = True
            timeout_message = (
                f"Request exceeded total timeout of {self.total_timeout} seconds."
            )
            logger.error(timeout_message)
            raise TimeoutError(timeout_message)

    def get(self, url, **kwargs) -> Response | None:
        """
        Sends a GET request to the specified URL, with a monitored timeout period.

        Args:
            url (str): The URL to send the GET request to.
            **kwargs: Additional arguments for `requests.get` (e.g., timeout settings).

        Returns:
            Optional[Response]: The HTTP response if successful and within the timeout,
            or None if an error occurs or the request exceeds the timeout.
        """
        timeout_thread = threading.Thread(target=self._timeout_handler, daemon=True)
        timeout_thread.start()

        try:
            response = requests.get(url, **kwargs)  # noqa: S113
            if not self.timed_out:  # Check if the request finished within the timeout
                self.timeout_event.set()  # Signal completion to the timeout handler
                return response
        except requests.exceptions.RequestException as e:
            msg = f"Request error: {e}"
            logger.exception(msg)

        return None
