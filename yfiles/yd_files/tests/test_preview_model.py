import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from yfiles.yd_files.models import File
from yfiles.yd_files.models import Preview
from yfiles.yd_files.tests.helpers.models import BaseModelFieldTest
from yfiles.yd_files.tests.helpers.models import BaseModelTest
from yfiles.yd_files.tests.helpers.models import BaseTestFieldRelated


class TestPreviewModel(BaseModelTest):
    model = Preview

    def test_file_attributes(self, instance):
        actual_attributes = [
            attr for attr in instance.__dict__ if not attr.startswith("_")
        ]
        expected_attributes = [
            "id",
            "file",
            "size_name",
            "preview_url",
        ]

        for attr in expected_attributes:
            assert hasattr(instance, attr), f"File should have attribute {attr}"

        assert len(actual_attributes) == len(expected_attributes), (
            f"Expected {len(expected_attributes)} attributes, "
            f"but found {len(actual_attributes)} in the File model instance."
        )

    def test_preview_string_representation(self, instance: Preview):
        obj_name = str(instance)
        assert obj_name == f"{instance.file.name}: {instance.size_name!r}"


class TestPreviewFieldFile(BaseTestFieldRelated):
    model = Preview
    related_model = File

    field_name = "file"
    field_type = models.ForeignKey
    related_name = "previews"
    db_index = True

    def test_on_delete_behavior(self):
        file_instance = File.objects.create(
            public_link="mock_public_link",
            path="/landing_page.png",
            name="landing_page.png",
            size=326985,
            type="file",
            mime_type="image/png",
            created="2021-02-03 13:46:08+03",
            modified="2021-02-03 13:46:08+03",
        )
        preview_instance = Preview.objects.create(
            file=file_instance,
            size_name="small",
            preview_url="http://example.com/preview.jpg",
        )
        file_instance.delete()
        # Verify that the Preview instance is also deleted (CASCADE behavior)
        with pytest.raises(ObjectDoesNotExist):
            Preview.objects.get(id=preview_instance.id)


class TestPreviewFieldSizeName(BaseModelFieldTest):
    model = Preview
    field_name = "size_name"
    field_type = models.fields.CharField
    max_length = 10


class TestPreviewFieldPreviewURL(BaseModelFieldTest):
    model = Preview
    field_name = "preview_url"
    field_type = models.fields.URLField
    max_length = 1024
