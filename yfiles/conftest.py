import pytest

from yfiles.users.models import User
from yfiles.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def _media_storage(settings, tmpdir) -> None:
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture(autouse=True)
def _static_files(settings, tmpdir) -> None:
    settings.STATICFILES_DIRS = []
    settings.STATIC_ROOT = tmpdir.mkdir("staticfiles")


@pytest.fixture
def user(db) -> User:
    return UserFactory()
