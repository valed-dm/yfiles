from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db import models
from model_bakery import baker

DATETIME_FIELDS = (models.DateTimeField, models.DateField, models.TimeField)


class BaseModelTest:
    model: models.Model = None
    instance_kwargs: dict[str, Any] = {}

    @pytest.fixture
    def instance(self) -> models.Model:
        return baker.make(self.model, **self.instance_kwargs)

    def test_is_django_model(self):
        assert issubclass(
            self.model,
            models.Model,
        ), f"{self.model} should be a Django model."

    def get_constraint_name(self, fields: list[str]) -> str:
        """Dynamically retrieve the name of the unique constraint for given fields."""
        for constraint in self.model._meta.constraints:  # noqa: SLF001
            if isinstance(constraint, models.UniqueConstraint) and set(
                constraint.fields,
            ) == set(fields):
                return constraint.name
        msg = f"No unique constraint found for fields {fields}"
        raise ValueError(msg)

    def assert_unique_constraint(self, constraint_name: str, **kwargs):
        """
        Helper to assert unique constraint with dynamically retrieved constraint name.
        """
        # Create the initial instance with provided unique fields
        _ = baker.make(self.model, **kwargs)
        # Try creating a duplicate instance and catch the IntegrityError
        with pytest.raises(IntegrityError, match=constraint_name):
            baker.make(self.model, **kwargs)


class BaseModelFieldTest:
    model: models.Model = None
    field_name: str = None
    field_type: type[models.Field] | tuple[type[models.Field], ...] = None

    null: bool = False
    blank: bool = False
    default: Any = models.fields.NOT_PROVIDED
    unique: bool = False
    db_index: bool = False
    auto_now: bool = False
    auto_now_add: bool = False
    max_length: int | None = None
    min_value: int | None = None
    exclude: str | None = None

    @property
    def field(self):
        return self.model._meta.get_field(self.field_name)  # noqa: SLF001

    def test_field_type(self):
        assert (
            type(self.field) is self.field_type
        ), f"{self.field_name} should be of type {self.field_type}."

    def test_null_blank(self):
        assert (
            self.field.null == self.null
        ), f"{self.field_name} null property mismatch."
        assert (
            self.field.blank == self.blank
        ), f"{self.field_name} blank property mismatch."

    def test_unique_and_index(self):
        assert (
            self.field.unique == self.unique
        ), f"{self.field_name} uniqueness property mismatch."
        assert (
            self.field.db_index == self.db_index
        ), f"{self.field_name} index property mismatch."

    def test_default_value(self):
        assert (
            self.field.default == self.default
        ), f"{self.field_name} default value mismatch."

    def test_max_length(self):
        if self.max_length:
            assert (
                self.field.max_length == self.max_length
            ), f"{self.field_name} max_length mismatch."
        else:
            pytest.skip(f"{self.field_name} has no max_length constraint.")

    def test_min_value_validation(self):
        if self.min_value is None:
            pytest.skip(f"{self.field_name} has no min_length constraint.")

        instance = baker.make(self.model)
        short_string = "a" * (self.min_value - 1)
        setattr(instance, self.field_name, short_string)
        with pytest.raises(ValidationError):
            instance.clean_fields(exclude=self.exclude)

        min_string = "a" * self.min_value
        setattr(instance, self.field_name, min_string)
        try:
            instance.clean_fields(exclude=self.exclude)
        except ValidationError:
            pytest.fail(f"{self.field_name} min_value constraint failed validation.")

    def test_datetime_auto_properties(self):
        if isinstance(self.field, DATETIME_FIELDS):
            assert (
                self.field.auto_now == self.auto_now
            ), f"{self.field_name} auto_now property mismatch."
            assert (
                self.field.auto_now_add == self.auto_now_add
            ), f"{self.field_name} auto_now_add property mismatch."
        else:
            pytest.skip(f"{self.field_name} is not a datetime field.")


class BaseTestFieldRelated(BaseModelFieldTest):
    related_model = None

    def test_has_correct_related_model(self):
        if self.field.is_relation:
            assert (
                self.field.related_model == self.related_model
            ), f"{self.field_name} related model mismatch."
        else:
            pytest.skip(f"{self.field_name} is not a related field.")
