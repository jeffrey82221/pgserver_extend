import sys
import tempfile

import pytest
import pgserver


@pytest.fixture
def tmp_postgres():
    tmp_pg_data = tempfile.mkdtemp()
    with pgserver.get_server(tmp_pg_data, cleanup_mode='delete') as pg:
        yield pg


@pytest.fixture
def require_extension(tmp_postgres):
    """ Returns a function that skips the test when the extension was not built into this wheel
    (e.g. AGE / pgsql-http / pgvectorscale on Windows, pg_textsearch on postgres < 17). """
    def _require(name: str) -> None:
        count = tmp_postgres.psql(
            f"SELECT count(*) FROM pg_available_extensions WHERE name = '{name}';")
        if count.split()[-3] == "0":
            pytest.skip(f"extension {name} is not built for this platform / postgres version")
    return _require
