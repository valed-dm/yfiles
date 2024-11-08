from http import HTTPStatus
from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse

from yfiles.yd_files.forms import YandexDiskPublicAccessLinkForm
from yfiles.yd_files.models import File
from yfiles.yd_files.models import Preview


class TestPublicAccessLinkFormView:
    @pytest.fixture
    def client(self):
        return Client()

    def test_get_request_renders_form(self, client):
        url = reverse("yd_files:public_access_link_form")
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        assert "form" in response.context
        assert isinstance(response.context["form"], YandexDiskPublicAccessLinkForm)
        assert "yd_files/public_access_link_form.html" in [
            t.name for t in response.templates
        ]

    def test_post_request_valid_form(self, client):
        url = reverse("yd_files:public_access_link_form")
        valid_data = {"public_link": "https://yadi.sk/some-valid-link"}
        response = client.post(url, data=valid_data)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == "files"
        assert client.session["public_link"] == valid_data["public_link"]

    def test_post_request_invalid_form(self, client):
        url = reverse("yd_files:public_access_link_form")
        invalid_data = {"public_link": ""}  # Empty link, which is invalid
        response = client.post(url, data=invalid_data)

        # Assert: Verify form re-rendering with errors
        assert response.status_code == HTTPStatus.OK
        assert "form" in response.context
        assert isinstance(response.context["form"], YandexDiskPublicAccessLinkForm)
        assert response.context["form"].errors  # Check that errors are present
        assert "yd_files/public_access_link_form.html" in [
            t.name for t in response.templates
        ]


class TestFolderDetailView:
    @pytest.fixture
    def mock_fetch_content(self):
        with patch("yfiles.yd_files.views.fetch_yandex_disk_content") as mock:
            yield mock

    @pytest.fixture
    def mock_save_files(self):
        with patch("yfiles.yd_files.views.save_files") as mock:
            yield mock

    @pytest.fixture
    def mock_create_previews(self):
        with patch("yfiles.yd_files.views.create_previews_for_folder") as mock:
            yield mock

    def test_folder_detail_success(
        self,
        client,
        mock_fetch_content,
        mock_save_files,
        mock_create_previews,
    ):
        # Mock Yandex Disk content response
        mock_fetch_content.return_value = {
            "_embedded": {
                "items": [
                    {
                        "public_link": "mock_public_link",
                        "path": "/landing_page.png",
                        "name": "landing_page.png",
                        "size": 326985,
                        "type": "file",
                        "mime_type": "image/png",
                        "created": "2021-02-03 13:46:08+03",
                        "modified": "2021-02-03 13:46:08+03",
                    },
                    {
                        "public_link": "mock_public_link",
                        "path": "/tribute_page.png",
                        "name": "tribute_page.png",
                        "size": 1260724,
                        "type": "file",
                        "mime_type": "image/png",
                        "created": "2021-02-03 13:46:08+03",
                        "modified": "2021-02-03 13:46:08+03",
                    },
                    {
                        "public_link": "mock_public_link",
                        "path": "/Logo",
                        "name": "Logo",
                        "size": 0,
                        "type": "dir",
                        "mime_type": "image/png",
                        "created": "2024-09-12 23:20:39+03",
                        "modified": "2024-09-12 23:20:39+03",
                    },
                ],
            },
        }

        # Mock session data for public link
        session = client.session
        session["public_link"] = "mock_public_link"
        session.save()

        # Create some file objects to test ORM filtering
        File.objects.create(
            public_link="mock_public_link",
            path="/test_folder/file1.pdf",
            name="file1.pdf",
            size=2460724,
            type="file",
            mime_type="application/pdf",
            created="2022-02-03 13:46:08+03",
            modified="2022-02-03 13:46:08+03",
        )
        File.objects.create(
            public_link="mock_public_link",
            path="/test_folder/subfolder",
            name="subfolder",
            size=0,
            type="dir",
            mime_type="mime_type_not_available",
            created="2022-02-03 13:46:08+03",
            modified="2022-02-03 13:46:08+03",
        )
        File.objects.create(
            public_link="mock_public_link",
            path="/test_folder/subfolder/nested_file.txt",
            name="nested_file.txt",
            size=3460724,
            type="file",
            mime_type="text/plain",
            created="2023-02-03 13:46:08+03",
            modified="2023-02-03 13:46:08+03",
        )

        # Make the request
        url = reverse(
            "yd_files:folder_detail",
            kwargs={"folder_path": "test_folder"},
        )
        response = client.get(url)

        # Assertions
        assert response.status_code == HTTPStatus.OK
        assert "yd_files/file_list.html" in [t.name for t in response.templates]
        assert "items" in response.context
        assert "folder_name" in response.context
        assert response.context["folder_name"] == "/test_folder"

        # Check that correct items are in the context
        items = response.context["items"]
        qty = 2
        assert len(items) == qty  # Only direct folder items, no nested files
        assert any(item.name == "file1.pdf" for item in items)
        assert any(item.name == "subfolder" for item in items)

        # Verify external calls
        mock_fetch_content.assert_called_once_with(
            link="mock_public_link",
            folder_path="/test_folder",
        )
        mock_save_files.assert_called_once()
        mock_create_previews.assert_called_once()

    def test_folder_not_found(self, client, mock_fetch_content):
        # Mock empty content response
        mock_fetch_content.return_value = {}

        # Mock session data for public link
        session = client.session
        session["public_link"] = "mock_public_link"
        session.save()

        # Make the request
        url = reverse(
            "yd_files:folder_detail",
            kwargs={"folder_path": "nonexistent_folder"},
        )
        response = client.get(url)

        # Assertions
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert b"Folder not found" in response.content


class TestFileDetailView:
    @pytest.fixture
    def file_with_previews(self):
        # Create a file with associated previews for testing
        file = File.objects.create(
            public_link="mock_public_link",
            path="/sample_file.png",
            name="sample_file.png",
            size=123456,
            type="file",
            mime_type="image/png",
            created="2023-10-01 12:00:00+03",
            modified="2023-10-01 12:00:00+03",
        )
        Preview.objects.create(
            file=file,
            size_name="XXL",
            preview_url="http://example.com/sample_preview_1024.png",
        )
        Preview.objects.create(
            file=file,
            size_name="XXXL",
            preview_url="http://example.com/sample_preview_2048.png",
        )
        return file

    def test_file_detail_view_success(self, client, file_with_previews):
        url = reverse("yd_files:file_detail", kwargs={"file_id": file_with_previews.id})
        response = client.get(url)

        # Assertions
        assert response.status_code == HTTPStatus.OK
        assert "yd_files/file_detail.html" in [t.name for t in response.templates]
        assert "file" in response.context
        assert "previews" in response.context
        assert response.context["file"] == file_with_previews

        # Check that the correct previews are in the context
        previews = response.context["previews"]
        qty = 2
        assert len(previews) == qty
        assert any(preview.size_name == "XXL" for preview in previews)
        assert any(preview.size_name == "XXXL" for preview in previews)

    def test_file_not_found(self, client):
        # Make a request for a non-existent file ID
        url = reverse("yd_files:file_detail", kwargs={"file_id": 9999})
        response = client.get(url)

        assert response.status_code == HTTPStatus.NOT_FOUND


class TestBulkDownloadView:
    @pytest.fixture
    def setup_files(self):
        files = [
            File.objects.create(
                public_link="mock_public_link",
                path="/test_folder/file1.pdf",
                name="file1.pdf",
                size=2460724,
                type="file",
                mime_type="application/pdf",
                created="2022-02-03 13:46:08+03",
                modified="2022-02-03 13:46:08+03",
            ),
            File.objects.create(
                public_link="mock_public_link",
                path="/test_folder/file2.pdf",
                name="file2.pdf",
                size=3460724,
                type="file",
                mime_type="application/pdf",
                created="2022-02-03 13:46:08+03",
                modified="2022-02-03 13:46:08+03",
            ),
        ]
        return [
            str(file.id) for file in files
        ]  # Return IDs as strings for form submission

    def test_bulk_download_success(self, client, setup_files):
        url = reverse("yd_files:bulk_download")

        # Mock the FileDownloadManager's download_files method
        with patch("yfiles.yd_files.views.FileDownloadManager") as mock_manager:
            mock_manager_instance = mock_manager.return_value
            # Simulate successful download
            mock_manager_instance.download_files.return_value = None

            # Make POST request with selected files
            response = client.post(url, {"selected_files": setup_files})

            # Assertions
            assert response.status_code == HTTPStatus.OK
            assert b"Files downloaded successfully." in response.content
            mock_manager.assert_called_once_with(
                setup_files,
            )  # Ensure manager is initialized with selected IDs
            mock_manager_instance.download_files.assert_called_once()

    def test_bulk_download_no_files_selected(self, client):
        url = reverse("yd_files:bulk_download")

        # Make POST request without any selected files
        response = client.post(url, {"selected_files": []})

        # Assertions
        assert response.status_code == HTTPStatus.OK
        assert b"No files selected" in response.content
