from django.db import models

from yfiles.yd_files.models import File
from yfiles.yd_files.tests.helpers.models import BaseModelFieldTest
from yfiles.yd_files.tests.helpers.models import BaseModelTest


class TestFileModel(BaseModelTest):
    model = File

    def test_file_attributes(self, instance):
        actual_attributes = [
            attr for attr in instance.__dict__ if not attr.startswith("_")
        ]
        expected_attributes = [
            "id",
            "public_link",
            "path",
            "name",
            "size",
            "type",
            "mime_type",
            "created",
            "modified",
        ]

        for attr in expected_attributes:
            assert hasattr(instance, attr), f"File should have attribute {attr}"

        assert len(actual_attributes) == len(expected_attributes), (
            f"Expected {len(expected_attributes)} attributes, "
            f"but found {len(actual_attributes)} in the File model instance."
        )

    def test_file_string_representation(self, instance: File):
        obj_name = str(instance)
        assert obj_name == f"{instance.public_link!r}: {instance.name!r}"

    def test_file_unique_public_link_name(self):
        # Dynamically retrieve the constraint name for "public_link" and "name"
        constraint_name = self.get_constraint_name(fields=["public_link", "name"])
        self.assert_unique_constraint(
            constraint_name,
            public_link="https://example.com",
            name="file_name",
        )


class TestFileFieldPublicLink(BaseModelFieldTest):
    model = File
    field_name = "public_link"
    field_type = models.fields.URLField
    max_length = 255


class TestFileFieldPath(BaseModelFieldTest):
    model = File
    field_name = "path"
    field_type = models.fields.CharField
    max_length = 1024


class TestFileFieldName(BaseModelFieldTest):
    model = File
    field_name = "name"
    field_type = models.fields.CharField
    max_length = 255


class TestFileFieldSize(BaseModelFieldTest):
    model = File
    field_name = "size"
    field_type = models.fields.BigIntegerField


class TestFileFieldType(BaseModelFieldTest):
    model = File
    field_name = "type"
    field_type = models.fields.CharField
    max_length = 50


class TestFileFieldMIMEType(BaseModelFieldTest):
    model = File
    field_name = "mime_type"
    field_type = models.fields.CharField
    max_length = 100


class TestFileFieldCreated(BaseModelFieldTest):
    model = File
    field_name = "created"
    field_type = models.fields.DateTimeField


class TestFileFieldModified(BaseModelFieldTest):
    model = File
    field_name = "modified"
    field_type = models.fields.DateTimeField
