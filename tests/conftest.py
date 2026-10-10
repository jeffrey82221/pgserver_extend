import platform
import sys
import tempfile

import pytest
import pgserver


@pytest.fixture
def tmp_postgres(request):
    tmp_pg_data = tempfile.mkdtemp()
    with pgserver.get_server(tmp_pg_data, cleanup_mode='delete') as pg:
        yield pg
        rep = getattr(request.node, "rep_call", None)
        if rep is not None and rep.failed:
            try:
                lines = pg.log.read_text().splitlines()[-60:]
                print("\n=== postgres server log (last 60 lines) ===\n" + "\n".join(lines))
            except Exception as err:  # never mask the real failure
                print(f"could not read postgres server log: {err}")


@pytest.fixture
def require_extension(tmp_postgres):
    """Returns a function that skips tests for extensions not built into this wheel."""
    def _require(name: str) -> None:
        count = tmp_postgres.psql(
            f"SELECT count(*) FROM pg_available_extensions WHERE name = '{name}';")
        if count.split()[-3] == "0":
            if sys.platform == "win32":
                pytest.skip(f"extension {name} is not built for Windows")
            if sys.platform == "darwin" and platform.machine() == "x86_64" and name == "http":
                pytest.skip("extension http is not built for Intel macOS")
            pytest.fail(f"expected extension {name} is missing from this wheel")
    return _require


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
