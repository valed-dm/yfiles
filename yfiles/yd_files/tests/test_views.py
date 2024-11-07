from http import HTTPStatus
from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse

from yfiles.yd_files.forms import YandexDiskPublicAccessLinkForm
from yfiles.yd_files.models import File


@pytest.mark.django_db
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


@pytest.mark.django_db
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
