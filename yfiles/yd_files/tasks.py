from celery import shared_task

from yfiles.yd_files.utils.download_parallel import download_parallel


@shared_task
def download_files_in_background(file_urls):
    download_parallel(file_urls)
