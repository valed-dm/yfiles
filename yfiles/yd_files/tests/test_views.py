from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import reverse

from yfiles.yd_files.forms import YandexDiskPublicAccessLinkForm


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
