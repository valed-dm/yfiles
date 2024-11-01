import logging
from collections.abc import Callable
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool

logger = logging.getLogger("yfiles")


def download_parallel(
    function: Callable[..., tuple[str, float | str, int | None]],
    items: list[tuple[any, ...]],
) -> list[tuple[str, float | str, int | None]]:
    """
    Processes items in parallel by applying a specified function to each item.
    Often used to download files or obtain fresh URLs in parallel.

    Args:
        function (Callable): The function to call for each item, e.g.,
            `obtain_fresh_file_url` or `download_url`.
            It should accept parameters in the form of `*args` matching each tuple in
            `items` and return a tuple containing the path or filename and either
            a duration in seconds or an error message.
        items (list): A list of tuples, where each tuple contains arguments for
            `function`.

    Returns:
        List[Tuple[str, Union[float, str]]]: A list of results from the function,
            with each entry as a tuple containing the filename or path and either
            the processing duration or an error message. pool.imap_unordered() returns
            results as they ready. Synchronization with args passed is necessary.
    """
    cpus = cpu_count()
    pool = ThreadPool(cpus - 1)

    results = pool.imap_unordered(lambda args: function(*args), items)

    processed_results = []
    for result in results:
        processed_results.append(result)
        path_or_filename = result[0]
        duration_or_error = result[1]
        if isinstance(duration_or_error, str):
            logger.error(
                "Failed to process %s: %s",
                path_or_filename,
                duration_or_error,
            )
        else:
            logger.info(
                "Processed %s in %0.2f seconds",
                path_or_filename,
                duration_or_error,
            )

    pool.close()
    pool.join()

    return processed_results
