import pytest
from django.test import override_settings
from ninja.testing import TestClient

from api.router import api
from api.auth import create_access_token


@pytest.fixture
def client():
    return TestClient(api)


@pytest.fixture
def author(db):
    from accounts.models import User
    return User.objects.create_user(
        email="author@example.com",
        username="testauthor",
        password="testpass123",
        role="author",
    )


@pytest.fixture
def reader(db):
    from accounts.models import User
    return User.objects.create_user(
        email="reader@example.com",
        username="testreader",
        password="testpass123",
        role="reader",
    )


@pytest.fixture
def author_token(author):
    return create_access_token(author.pk)


@pytest.fixture
def reader_token(reader):
    return create_access_token(reader.pk)


@pytest.fixture
def published_post(db, author):
    from blog.models import Post
    return Post.objects.create(
        author=author,
        title="Hello World",
        content="Some content here.",
        excerpt="Short excerpt.",
        status=Post.Status.PUBLISHED,
    )


@pytest.fixture
def draft_post(db, author):
    from blog.models import Post
    return Post.objects.create(
        author=author,
        title="Draft Post",
        content="Draft content.",
        status=Post.Status.DRAFT,
    )


@pytest.fixture(autouse=True)
def use_dummy_cache(settings):
    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
    settings.CELERY_TASK_ALWAYS_EAGER = True
