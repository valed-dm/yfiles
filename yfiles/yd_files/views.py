import logging
from time import time
from urllib.parse import quote

from django.db.models.query_utils import Q
from django.http import HttpResponseNotFound
from django.http import HttpResponseRedirect
from django.http.response import HttpResponse
from django.shortcuts import render

from yfiles.yd_files.forms import YandexDiskPublicAccessLinkForm
from yfiles.yd_files.models import File
from yfiles.yd_files.utils.download_parallel import download_parallel
from yfiles.yd_files.utils.download_url import download_url
from yfiles.yd_files.utils.fetch_yandex_disk_content import fetch_yandex_disk_content
from yfiles.yd_files.utils.obtain_url import obtain_fresh_file_url_from_yandex_disk
from yfiles.yd_files.utils.save_file_and_previews import save_file_and_previews

logger = logging.getLogger("yfiles")


def public_access_link_form_view(request) -> HttpResponse:
    """
    Handles the form submission to fetch Y_Disk data and store it in the session.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: Redirect to the file list view or render the form if GET.
    """
    if request.method == "POST":
        form = YandexDiskPublicAccessLinkForm(request.POST)
        if form.is_valid():
            public_link = form.cleaned_data["public_link"]
            # Store the public link in the session
            request.session["public_link"] = public_link

            # Fetch Yandex Disk data
            files_data = fetch_yandex_disk_content(link=public_link)
            if files_data:
                items = files_data.get("_embedded", {}).get("items", [])
                save_file_and_previews(file_data_list=items, public_link=public_link)
                return HttpResponseRedirect("files")
    else:
        form = YandexDiskPublicAccessLinkForm()

    return render(request, "yd_files/public_access_link_form.html", {"form": form})


def file_list_view(request) -> HttpResponse:
    """
    Displays a list of files and top-level folders.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: Rendered file list and folder view.
    """
    public_link = request.session.get("public_link")

    # Get all folders (type='dir')
    all_folders = File.objects.filter(public_link=public_link, type="dir").values_list(
        "path",
        flat=True,
    )

    # Build exclusion criteria for enclosed folders
    folders_exclude_criteria = Q()
    for folder_path in all_folders:
        folders_exclude_criteria |= Q(path__startswith=folder_path + "/")

    # Fetch top-level folders only (those not enclosed in other folders)
    top_level_folders = File.objects.filter(
        public_link=public_link,
        type="dir",
    ).exclude(folders_exclude_criteria)

    # Build exclusion criteria for files in folders
    files_exclude_criteria = Q()
    for folder_path in all_folders:
        files_exclude_criteria |= Q(path__startswith=folder_path)

    # Fetch all files from the database and their previews
    files = File.objects.filter(public_link=public_link).exclude(files_exclude_criteria)
    return render(
        request,
        "yd_files/file_list.html",
        {"files": files, "folders": top_level_folders},
    )


def file_detail_view(request, file_id: int) -> HttpResponse:
    """
    Displays detailed information for a specific file.

    Args:
        request (HttpRequest): The request object.
        file_id (int): The ID of the file.

    Returns:
        HttpResponse: Rendered file detail view.
    """
    file = File.objects.get(id=file_id)
    previews = file.previews.all()
    return render(
        request,
        "yd_files/file_detail.html",
        {"file": file, "previews": previews},
    )


def folder_detail_view(request, folder_path: str) -> HttpResponse:
    """
    Displays the contents of a specific folder.

    Args:
        request (HttpRequest): The request object.
        folder_path (str): The path of the folder.

    Returns:
        HttpResponse: Rendered folder detail view or error if folder not found.
    """
    folder_path = "/" + folder_path
    public_link = request.session.get("public_link")
    folder_path_encoded = quote(folder_path)

    folder_files_data = fetch_yandex_disk_content(
        link=public_link,
        folder_path=folder_path_encoded,
    )

    folder_files_data = folder_files_data.get("_embedded", {})
    if folder_files_data and "items" in folder_files_data:
        items = folder_files_data.get("items", [])
        save_file_and_previews(file_data_list=items, public_link=public_link)

        # Filter files from the database by folder path
        files = File.objects.filter(path__startswith=folder_path)
        return render(
            request,
            "yd_files/folder_detail.html",
            {"files": files, "folder_path": folder_path},
        )

    return HttpResponseNotFound("Folder not found.")


def bulk_download_view(request) -> HttpResponse:
    if request.method == "POST":
        selected_file_ids = request.POST.getlist("selected_files")
        files_to_download = File.objects.filter(id__in=selected_file_ids)

        # Prepare a list of (public_link, path) tuples for obtaining fresh URLs
        file_data = [(file.public_link, file.path) for file in files_to_download]

        start_url_fetch_time = time()
        # Obtain fresh URLs in parallel
        fresh_urls = download_parallel(
            obtain_fresh_file_url_from_yandex_disk,
            file_data,
        )
        url_fetch_duration = time() - start_url_fetch_time
        logger.info(
            "Total elapsed time for obtaining fresh URLs: %0.2f seconds",
            url_fetch_duration,
        )

        start_download_time = time()
        # Download files concurrently using the fresh URLs
        download_parallel(download_url, fresh_urls)
        download_duration = time() - start_download_time
        logger.info(
            "Total elapsed time for downloading files: %0.2f seconds",
            download_duration,
        )

        return HttpResponse("Files downloaded successfully.")

    return HttpResponse("No files selected")
