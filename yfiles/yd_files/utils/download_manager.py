import logging
from multiprocessing import cpu_count

from yfiles.yd_files.models import File
from yfiles.yd_files.tasks import download_file_in_background
from yfiles.yd_files.utils.download_file import download_url
from yfiles.yd_files.utils.download_parallel import download_parallel
from yfiles.yd_files.utils.generate_filename import generate_filename_from_download_url
from yfiles.yd_files.utils.obtain_fresh_download_url import (
    obtain_fresh_file_download_url,
)

logger = logging.getLogger("yfiles")


class FileDownloadManager:
    """
    Manages the downloading of files based on size criteria, using
    sequential, parallel, or background strategies to optimize performance.

    Attributes:
        files_to_download (QuerySet): QuerySet of files to be downloaded.
        size_threshold (int): Threshold size in bytes to distinguish between
            large and small files. Default is 50 MB.
        file_data (List[Tuple[str, str, int, int]]): List of tuples containing
            file URLs, paths, sizes, and unique IDs for each file.
        fresh_urls_with_size (List[Tuple[str, int]]): Fresh URLs paired with
            file sizes.
        available_cores (int): Number of available CPU cores.
    """

    def __init__(
        self,
        selected_file_ids: list[int],
        size_threshold: int = 50 * 1024 * 1024,
    ):
        """
        Initialize the FileDownloadManager with selected file IDs and a size threshold.

        Args:
            selected_file_ids (List[int]): IDs of the files to download.
            size_threshold (int): Size in bytes to separate small and large files.
                Defaults to 50 MB.
        """
        self.files_to_download = File.objects.filter(id__in=selected_file_ids)
        self.size_threshold = size_threshold
        self.file_data = [
            (file.public_link, file.path, file.size, file.id)
            for file in self.files_to_download
        ]
        self.fresh_urls_with_size = self._obtain_fresh_urls_with_size()
        self.available_cores = cpu_count()

    def _obtain_fresh_urls_with_size(self) -> list[tuple[str, int]]:
        """
        Obtain fresh URLs paired with file sizes in parallel.

        Returns:
            list[tuple[str, int]]: A list of tuples with each tuple containing
            a fresh URL and the corresponding file size.
        """
        fresh_urls = download_parallel(
            obtain_fresh_file_download_url,
            [(fd[0], fd[1], fd[3]) for fd in self.file_data],
        )
        fresh_urls_by_id = {fresh_url[2]: fresh_url[0] for fresh_url in fresh_urls}
        return [(fresh_urls_by_id[fd[3]], fd[2]) for fd in self.file_data]

    def get_large_files(self) -> list[str]:
        """
        Get URLs for large files exceeding the size threshold.

        Returns:
            list[str]: URLs of files larger than the size threshold.
        """
        return [
            url for url, size in self.fresh_urls_with_size if size > self.size_threshold
        ]

    def get_small_files(self) -> list[str]:
        """
        Get URLs for small files at or below the size threshold.

        Returns:
            list[str]: URLs of files smaller than or equal to the size threshold.
        """
        return [
            url
            for url, size in self.fresh_urls_with_size
            if size <= self.size_threshold
        ]

    def download_files(self):
        """
        Executes the file download strategy. Large files are handled
        in the background with Celery, while small files are downloaded
        either sequentially or in parallel.
        """
        large_files = self.get_large_files()
        small_files = self.get_small_files()

        if large_files:
            for url in large_files:
                filename = generate_filename_from_download_url(url)
                download_file_in_background.delay(url=url, filename=filename)
                logger.info("Downloading %s in background via Celery", filename)

        if len(small_files) <= self.available_cores:
            for url in small_files:
                filename = generate_filename_from_download_url(url)
                logger.info("Downloaded %s sequentially", filename)
                download_url(url=url, filename=filename)
        else:
            logger.info("Parallel downloading %d files", len(small_files))
            download_parallel(
                download_url,
                [
                    (
                        url,
                        generate_filename_from_download_url(url),
                    )
                    for url in small_files
                ],
            )
