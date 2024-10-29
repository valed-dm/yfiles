"""yd_files models"""

from django.db import models

from yfiles.yd_files.utils.obtain_url import obtain_fresh_file_url_from_yandex_disk


class File(models.Model):
    """
    Represents a file with metadata.

    Attributes:
        public_link (str): Public link to the directory containing the file.
        path (str): Path to the file within the public link.
        name (str): Name of the file.
        size (int): Size of the file in bytes.
        type (str): Type of the file (e.g., 'image', 'document').
        mime_type (str): MIME type of the file.
        created (datetime): Timestamp when the file was created.
        modified (datetime): Timestamp when the file was last modified.
    """

    public_link = models.URLField(max_length=255)
    path = models.CharField(max_length=1024)
    name = models.CharField(max_length=255)
    size = models.BigIntegerField()
    type = models.CharField(max_length=50)
    mime_type = models.CharField(max_length=100)
    created = models.DateTimeField()
    modified = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["public_link", "name"],
                name="unique_public_link_name",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.public_link!r}: {self.name!r}"

    def get_file_url(self):
        # Logic to get file_url dynamically from Yandex Disk API
        return obtain_fresh_file_url_from_yandex_disk(
            public_link=self.public_link,
            path=self.path,
        )


class Preview(models.Model):
    """
    Represents a preview image for a file.

    Attributes:
        file (File): The file that this preview belongs to.
        size_name (str): Name or size of the preview (e.g., 'small', 'medium').
        preview_url (str): URL where the preview image can be viewed.
    """

    file = models.ForeignKey(File, related_name="previews", on_delete=models.CASCADE)
    size_name = models.CharField(max_length=10)
    preview_url = models.URLField(max_length=1024)

    def __str__(self) -> str:
        return f"{self.file.name}: {self.size_name!r}"
