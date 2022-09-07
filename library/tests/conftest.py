import os
import subprocess  # noqa: S404

import pytest
from pytest_factoryboy import register

from booklogger import settings
from library.factories import (  # noqa: F401
    AuthorFactory,
    BookFactory,
    TagFactory,
    UserFactory,
)

register(AuthorFactory)
register(BookFactory)
register(TagFactory)
register(UserFactory)


@pytest.fixture(autouse=True)
def unset_goodreads_key(settings):
    settings.GOODREADS_KEY = None


@pytest.fixture
def goodreads_key(settings):
    settings.GOODREADS_KEY = "TEST_FAKE"


@pytest.fixture
def read_book(book, transactional_db):
    book.start_reading()
    book.finish_reading()

    return book


@pytest.fixture
def read_book_factory(book_factory, *args, **kwargs):
    def _book_factory(*args, **kwargs):
        book = book_factory(*args, **kwargs)
        book.start_reading()
        book.finish_reading()
        return book

    yield _book_factory


@pytest.fixture(scope="session")
def django_db_modify_db_settings(request, worker_id, django_db_modify_db_settings):
    if "DYNO" in os.environ:
        return

    docker_was_running = False

    if "booklogger-postgres" in str(
        subprocess.run(  # noqa: S603, S607
            ["docker-compose", "ps"], capture_output=True
        ).stdout
    ):
        docker_was_running = True
    else:
        if worker_id in ["master", "gw0"]:
            subprocess.run(  # noqa: S603, S607
                ["docker-compose", "up", "-d", "postgres"]
            )

        subprocess.run(
            f"while ! pg_isready -h {settings.DATABASES['default']['HOST']}; do sleep 1; done",
            shell=True,  # noqa: S602
            capture_output=True,
        )

    def teardown_database():
        if not docker_was_running and (
            len(
                str(
                    subprocess.run(  # noqa: S607
                        ["ps | grep 'pytest-xdist running'"],
                        capture_output=True,
                        shell=True,  # noqa: S602
                    ).stdout
                ).splitlines()
            )
            < 1
        ):
            subprocess.run(["docker-compose", "down"])  # noqa: S603, S607

    request.addfinalizer(teardown_database)
