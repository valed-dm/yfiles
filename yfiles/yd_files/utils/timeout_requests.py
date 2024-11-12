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
        Monitors the total timeout duration for the request.

        If the request does not complete within the specified timeout,
        it sets the `timed_out` flag to True and logs an error message.
        This function is run in a separate thread to allow the main request
        to proceed while monitoring the total timeout.
        """
        if not self.timeout_event.wait(self.total_timeout):
            self.timed_out = True
            msg = f"Request exceeded total timeout of {self.total_timeout} seconds."
            logger.error(msg)

    def get(self, url, **kwargs) -> Response | None:
        """
        Sends a GET request to the specified URL, with a monitored timeout period.

         This method starts a separate thread that monitors the total timeout period.
        If the request completes within the allowed time, the response is returned.
        Otherwise, a `TimeoutError` is raised. Any other exceptions during the request
        will be logged, and None will be returned.

        Args:
            url (str): The URL to send the GET request to.
            **kwargs: Additional arguments for `requests.get` (e.g., timeout settings).

        Returns:
            Optional[Response]: The HTTP response if successful and within the timeout,
            or None if an error occurs or the request exceeds the timeout.

         Returns:
            Optional[Response]: The HTTP response if successful and within the timeout,
            or None if an error occurs or the request exceeds the timeout.

         Raises:
            TimeoutError: If the request exceeds the specified total timeout.
        """
        timeout_thread = threading.Thread(target=self._timeout_handler, daemon=True)
        timeout_thread.start()

        try:
            response = requests.get(url, **kwargs)  # noqa: S113
            if self.timed_out:
                msg = f"Request exceeded total timeout of {self.total_timeout} seconds."
                raise TimeoutError(msg)
            self.timeout_event.set()  # Signal completion to the timeout handler
            return response  # noqa: TRY300

        except requests.exceptions.RequestException as e:
            msg = f"Request error: {e}"
            logger.exception(msg)

        return None
