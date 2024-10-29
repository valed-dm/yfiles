"""
yd_files forms.

This module contains forms used in the yd_files application, specifically for
interacting with Yandex Disk links.

Classes:
- `YandexDiskPublicAccessLinkForm`: A form for entering a Yandex Disk public link.
"""

from django import forms


class YandexDiskPublicAccessLinkForm(forms.Form):
    """
    A form for submitting a Yandex Disk public link.

    This form is used to capture and validate the Yandex Disk public link provided
    by the user. The link will be used to fetch and manage files from Yandex Disk.

    Fields:
    - `public_link`: A CharField to input the Yandex Disk public link. The maximum
      length of the link is limited to 500 characters.
    """

    public_link = forms.CharField(label="Yandex Disk Files Public Link", max_length=500)
