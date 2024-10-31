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
    def __init__(
        self,
        selected_file_ids: list[int],
        size_threshold: int = 50 * 1024 * 1024,
    ):
        self.files_to_download = File.objects.filter(id__in=selected_file_ids)
        self.size_threshold = size_threshold
        self.file_data = [
            (file.public_link, file.path, file.size, file.id)
            for file in self.files_to_download
        ]
        self.fresh_urls_with_size = self._obtain_fresh_urls_with_size()
        self.available_cores = cpu_count()

    def _obtain_fresh_urls_with_size(self) -> list[tuple[str, int]]:
        # Obtain fresh URLs in parallel and pair with sizes
        fresh_urls = download_parallel(
            obtain_fresh_file_download_url,
            # fd[0] is the link, fd[1] is the path, fd[3] is the unique ID
            [(fd[0], fd[1], fd[3]) for fd in self.file_data],
        )
        # Use the fresh_url[2] unique ID as the key
        fresh_urls_by_id = {fresh_url[2]: fresh_url[0] for fresh_url in fresh_urls}
        return [(fresh_urls_by_id[fd[3]], fd[2]) for fd in self.file_data]

    def get_large_files(self) -> list[str]:
        # Extract URLs for large files based on the size threshold
        return [
            url for url, size in self.fresh_urls_with_size if size > self.size_threshold
        ]

    def get_small_files(self) -> list[str]:
        # Extract URLs for small files based on the size threshold
        return [
            url
            for url, size in self.fresh_urls_with_size
            if size <= self.size_threshold
        ]

    def download_files(self):
        # Decide download strategy based on file sizes and available cores
        large_files = self.get_large_files()
        small_files = self.get_small_files()

        if large_files:
            for url in large_files:
                filename = generate_filename_from_download_url(url)
                download_file_in_background.delay(url=url, filename=filename)
                logger.info("Downloading %s in background via Celery", filename)

        if len(small_files) <= self.available_cores:
            # Download small files sequentially
            for url in small_files:
                download_url(url)
        else:
            # Download small files in parallel
            logger.info("Parallel downloading %d files", len(small_files))
            download_parallel(download_url, [(url,) for url in small_files])
