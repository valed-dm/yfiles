import pytest

from yfiles.yd_files.forms import YandexDiskPublicAccessLinkForm


@pytest.fixture
def valid_data():
    return {"public_link": "https://disk.yandex.com/public/valid_link"}


@pytest.fixture
def invalid_data_empty():
    return {"public_link": ""}


@pytest.fixture
def invalid_data_long():
    return {"public_link": "https://" + "a" * 495}


def test_form_valid_data(valid_data):
    """Test form with valid data"""
    form = YandexDiskPublicAccessLinkForm(data=valid_data)
    assert form.is_valid(), "The form should be valid with correct input."


def test_form_empty_data(invalid_data_empty):
    """Test form with empty data"""
    form = YandexDiskPublicAccessLinkForm(data=invalid_data_empty)
    assert not form.is_valid(), "The form should be invalid if the link is empty."
    assert (
        "public_link" in form.errors
    ), "Error should be present for empty public_link."


def test_form_long_data(invalid_data_long):
    """Test form with data exceeding max_length"""
    form = YandexDiskPublicAccessLinkForm(data=invalid_data_long)
    assert (
        not form.is_valid()
    ), "The form should be invalid if the link exceeds 500 characters."
    assert (
        "public_link" in form.errors
    ), "Error should be present for too long public_link."


def test_form_field_attributes():
    """Test form field attributes for public_link"""
    form = YandexDiskPublicAccessLinkForm()
    public_link_field = form.fields["public_link"]

    max_length = 500
    assert public_link_field.max_length == max_length, "max_length should be 500."
    assert (
        public_link_field.label == "Yandex Disk Files Public Link"
    ), "Label should be set."
    assert (
        public_link_field.widget.attrs["class"] == "form-control"
    ), "Class should be form-control."
    assert (
        public_link_field.widget.attrs["placeholder"] == "Yandex Disk Files Public Link"
    ), "Placeholder should be set."
    assert (
        public_link_field.help_text == "Enter the public link to Yandex Disk files."
    ), "Help text should be set."
