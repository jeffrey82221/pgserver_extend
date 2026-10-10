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


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(autouse=True)
def _dump_server_log_on_failure(request):
    """ When a test fails, print the tail of the log of every server it used. """
    yield
    rep = getattr(request.node, "rep_call", None)
    if rep is None or not rep.failed or "tmp_postgres" not in request.fixturenames:
        return
    pg = request.getfixturevalue("tmp_postgres")
    try:
        lines = pg.log.read_text().splitlines()[-60:]
        print("\n=== postgres server log (last 60 lines) ===\n" + "\n".join(lines))
    except Exception as err:  # never mask the real failure
        print(f"could not read postgres server log: {err}")
