from urllib.parse import quote

from django.db.models import Case
from django.db.models import CharField
from django.db.models import Value
from django.db.models import When
from django.db.models.query_utils import Q
from django.http import HttpResponseNotFound
from django.http.response import HttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from yfiles.yd_files.forms import YandexDiskPublicAccessLinkForm
from yfiles.yd_files.models import File
from yfiles.yd_files.utils.download_manager import FileDownloadManager
from yfiles.yd_files.utils.fetch_yandex_disk_content import fetch_yandex_disk_content
from yfiles.yd_files.utils.save_file_and_previews import create_previews_for_folder
from yfiles.yd_files.utils.save_file_and_previews import save_files


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
            request.session["public_link"] = public_link
            return HttpResponseRedirect("files")
    else:
        form = YandexDiskPublicAccessLinkForm()

    return render(request, "yd_files/public_access_link_form.html", {"form": form})


def folder_detail_view(request, folder_path: str = "") -> HttpResponse:
    """
    Displays the contents of a specific folder.

    Args:
        request (HttpRequest): The request object.
        folder_path (str): The path of the folder.

    Returns:
        HttpResponse: Rendered folder detail view or error if folder not found.
    """
    public_link = request.session.get("public_link")
    folder_path = "/" + folder_path.strip("/") if folder_path else ""
    folder_path_encoded = quote(folder_path)

    folder_files_data = fetch_yandex_disk_content(
        link=public_link,
        folder_path=folder_path_encoded,
    ).get("_embedded", {})

    if folder_files_data and "items" in folder_files_data:
        items = folder_files_data.get("items")
        save_files(
            file_data_list=items,
            public_link=public_link,
            folder_path=folder_path,
        )

        create_previews_for_folder(
            public_link=public_link,
            folder_path=folder_path,
            previews_data=[
                {item.get("name"): item.get("sizes", None)} for item in items
            ],
        )

        yandex_disk_data = (
            File.objects.filter(
                path__startswith=folder_path + "/",
                public_link=public_link,
            )
            .exclude(
                Q(
                    path__regex=rf"^{folder_path}/[^/]+/[^/]+",
                ),  # Exclude nested folders and files in nested folders
            )
            .annotate(
                item_type=Case(
                    When(type="dir", then=Value("folder")),
                    default=Value("file"),
                    output_field=CharField(),
                ),
            )
        )

        return render(
            request,
            "yd_files/file_list.html",
            {
                "items": yandex_disk_data,
                "folder_name": folder_path or "/",
            },
        )

    return HttpResponseNotFound("Folder not found.")


def file_detail_view(request, file_id: int) -> HttpResponse:
    """
    Displays detailed information for a specific file.

    Args:
        request (HttpRequest): The request object.
        file_id (int): The ID of the file.

    Returns:
        HttpResponse: Rendered file detail view or 404 if file not found.
    """
    file = get_object_or_404(File, id=file_id)
    previews = file.previews.all()
    return render(
        request,
        "yd_files/file_detail.html",
        {"file": file, "previews": previews},
    )


def bulk_download_view(request) -> HttpResponse:
    if request.method == "POST":
        selected_file_ids = request.POST.getlist("selected_files")
        manager = FileDownloadManager(selected_file_ids)

        # Execute download based on the size criteria
        manager.download_files()

        return HttpResponse("Files downloaded successfully.")

    return HttpResponse("No files selected")
