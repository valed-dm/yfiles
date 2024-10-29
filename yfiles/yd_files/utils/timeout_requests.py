import logging
import threading

import requests

logger = logging.getLogger("yfiles")


class TimeoutRequest:
    def __init__(self, total_timeout: int):
        self.total_timeout = total_timeout
        self.timeout_event = threading.Event()
        self.timed_out = False

    def _timeout_handler(self):
        if not self.timeout_event.wait(
            self.total_timeout,
        ):  # Wait for either timeout or completion
            self.timed_out = True
            timeout_message = (
                f"Request exceeded total timeout of {self.total_timeout} seconds."
            )
            logger.error(timeout_message)
            raise TimeoutError(timeout_message)

    def get(self, url, **kwargs):
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
