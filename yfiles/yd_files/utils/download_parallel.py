import logging
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool

logger = logging.getLogger("yfiles")


def download_parallel(function, items):
    """
    Downloads files or obtains URLs in parallel using a specified function.

    Args:
        function (callable): The function to call for each item
        (e.g., obtain_fresh_file_url, download_url).
        items (list): A list of items (URLs or data for processing).

    Returns:
        list: Results of the processing.
    """
    cpus = cpu_count()
    pool = ThreadPool(cpus - 1)

    results = pool.imap_unordered(lambda args: function(*args), items)

    processed_results = []
    for result in results:
        processed_results.append(result)
        path_or_filename, duration_or_error = result
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
