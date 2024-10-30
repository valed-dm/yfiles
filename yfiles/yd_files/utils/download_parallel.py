import logging
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
from time import time

logger = logging.getLogger("yfiles")


def download_parallel(function, items):
    """
    Downloads files or obtains URLs in parallel using a specified function,
    with detailed timing logs for each phase.

    Args:
        function (callable): The function to call for each item
        (e.g., obtain_fresh_file_url, download_url).
        items (list): A list of items (URLs or data for processing).

    Returns:
        list: Results of the processing.
    """
    cpus = cpu_count()
    pool = ThreadPool(cpus - 2)

    # Start total timer for the entire parallel execution phase
    start_total_time = time()
    logger.info("Starting download_parallel with %d items", len(items))

    results = pool.imap_unordered(lambda args: function(*args), items)

    processed_results = []
    individual_durations_sum = 0  # For summing individual download times

    # Measure individual item processing start and end times
    for _, result in enumerate(results, start=1):
        item_start_time = time()  # Track the start time of each item
        processed_results.append(result)
        path_or_filename, duration_or_error = result

        # Calculate individual item processing duration
        item_elapsed_time = time() - item_start_time

        if isinstance(duration_or_error, str):
            logger.error(
                "Failed to process %s: %s (item took %0.5f seconds)",
                path_or_filename,
                duration_or_error,
                item_elapsed_time,
            )
        else:
            individual_durations_sum += duration_or_error
            logger.info(
                "Processed %s in %0.2f seconds (actual processing took %0.5f seconds)",
                path_or_filename,
                duration_or_error,
                item_elapsed_time,
            )

    # End total timer after processing all results
    total_elapsed_time = time() - start_total_time
    pool.close()
    pool.join()

    # Log the timing comparisons
    logger.info(
        "Total elapsed time for all downloads: %0.2f seconds",
        total_elapsed_time,
    )
    logger.info(
        "Sum of individual download durations: %0.2f seconds",
        individual_durations_sum,
    )

    return processed_results
