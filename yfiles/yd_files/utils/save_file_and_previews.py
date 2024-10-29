from django.db import IntegrityError

from yfiles.yd_files.models import File
from yfiles.yd_files.models import Preview


def save_file_and_previews(file_data_list: list[dict], public_link: str) -> None:
    """
    Saves file data and its associated previews to the database.

    Args:
        file_data_list (List[Dict]): List of file data dictionaries.
        public_link (str): The public link associated with the files.

    Returns:
        None
    """
    for file_data in file_data_list:
        try:
            # Attempt to create the file entry
            file_obj, created = File.objects.get_or_create(
                public_link=public_link,
                path=file_data.get("path", None),
                name=file_data.get("name", None),
                size=file_data.get("size", 0),
                type=file_data.get("type", "type_not_available"),
                mime_type=file_data.get("mime_type", "mime_type_not_available"),
                created=file_data.get("created", None),
                modified=file_data.get("modified", None),
            )

            # If the file was created, bulk create previews
            if created:
                previews_to_create = [
                    Preview(
                        file=file_obj,
                        size_name=preview["name"],
                        preview_url=preview["url"],
                    )
                    for preview in file_data.get("sizes", [])
                ]

                if previews_to_create:
                    Preview.objects.bulk_create(previews_to_create)

        # To avoid duplicated db data
        except IntegrityError:
            pass
