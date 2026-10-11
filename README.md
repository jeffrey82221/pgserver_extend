![Python Version](https://img.shields.io/badge/python-3.9%20to%203.15-blue)
![Postgres Version](https://img.shields.io/badge/PostgreSQL-18.6-blue)

![Linux Support](https://img.shields.io/badge/Linux%20Support-manylinux-green)
![macOS Apple Silicon Support >=11](https://img.shields.io/badge/macOS%20Apple%20Silicon%20Support-%E2%89%A511(BigSur)-green)
![macOS Intel Support => 14](https://img.shields.io/badge/macOS%20Intel%20Support-%E2%89%A514-green)
![Windows Support >= 2022](https://img.shields.io/badge/Windows%20AMD64%20Support-%E2%89%A52022-green)

[![License](https://img.shields.io/badge/License-Apache%202.0-darkblue.svg)](https://opensource.org/licenses/Apache-2.0)
[![PyPI Package](https://img.shields.io/pypi/v/pgserver-extend?color=darkorange)](https://pypi.org/project/pgserver-extend)
![PyPI - Downloads](https://img.shields.io/pypi/dm/pgserver-extend)


<p align="center">
  <img src="https://raw.githubusercontent.com/orm011/pgserver/main/pgserver_square_small.png"/>
</p>

# pgserver-extend: pip-installable embedded PostgreSQL server with useful extensions for Python apps

`pgserver-extend` is a fork of the original `pgserver` project. It keeps the embedded PostgreSQL workflow that makes local Postgres easy to use from Python, while broadening the set of bundled PostgreSQL extensions beyond `pgvector` alone.

This package is designed for Python apps that want a self-contained, pip-installable PostgreSQL runtime without requiring users to manage a system Postgres installation. The goal is the same convenience as an embedded database (for example, SQLite), while providing a more featureful Postgres environment for application work.

If you are familiar with the original `pgserver` project, this repository is the forked variant that adds more useful extensions and keeps the same embedded-server workflow. The Python API remains compatible with the `pgserver` module name in this codebase, but the project itself is `pgserver-extend` rather than the original upstream project.

To achieve this, `pgserver-extend` provides:
  * Python binary wheels for multiple platforms with bundled PostgreSQL binaries
  * convenience Python methods that initialize the database and manage the server lifecycle, including edge cases such as Docker, constrained environments, Google Colab, port conflicts, and existing PostgreSQL instances
  * a set of bundled PostgreSQL extensions for application development, not only [pgvector](https://github.com/pgvector/pgvector) but also useful extensions such as Apache AGE, pgsql-http, pgvectorscale, and pg_textsearch

This package is not a rebranding of the original `pgserver`; it is a forked, extended version that builds on the upstream work while adding additional embedded Postgres capabilities.

## Supported platforms, Python versions and Postgres extensions
Wheels bundle PostgreSQL 18.6. Data below comes from the CI workflow (`.github/workflows/build-and-test.yml`), which builds each wheel and runs the pytest suite against it.

| Platform | Minimum OS (wheel tag) | Python versions | pgvector | Apache AGE | pgsql-http | pgvectorscale | pg_textsearch |
|---|---|---|:-:|:-:|:-:|:-:|:-:|
| Linux x86_64 | glibc ≥ 2.28 (`manylinux_2_28_x86_64`) | 3.9 – 3.15 | ✅ | ✅ | ✅ | ✅ | ✅ |
| macOS Apple Silicon | macOS ≥ 11.0 (`macosx_11_0_arm64`) | 3.9 – 3.15 | ✅ | ✅ | ✅ | ✅ | ✅ |
| macOS Intel | macOS ≥ 14.0 (`macosx_14_0_x86_64`) | 3.9 – 3.15 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Windows x86_64 | `win_amd64` | 3.9 – 3.15 | ✅ | ❌ | ❌ | ❌ | ❌ |

Notes: ❌ means the extension is not built for that platform. Python 3.15 is a release candidate in CI. Not built: Python 3.8, PyPy, free-threaded builds, musllinux, 32-bit and Windows ARM. CI runs on the newest runner images only (ubuntu-latest, macos-26, macos-26-intel, windows-2022).

## Basic summary:
* _Pip-installable binaries_: built and tested on manylinux, macOS, and Windows.
* _No sudo or admin rights needed_: does not require `root` privileges or `sudo`.
* but... _can handle root_: in some environments your Python app runs as root, for example Docker or Google Colab; `pgserver-extend` handles this case.
* _Simpler initialization_: `pgserver.get_server(MY_DATA_DIR)` initializes the data directory and starts the server when needed, so you do not need to understand `initdb`, `pg_ctl`, or port conflicts.
* _Convenient cleanup_: server-process cleanup is handled for you. When the process using the embedded server ends, the server shuts down, including when multiple independent processes call `pgserver.get_server(MY_DATA_DIR)` on the same data directory; the last process cleans up.
* For lower-level control, wrappers to binaries such as `initdb`, `pg_ctl`, `psql`, and `pg_config` are included, along with headers for building additional extensions against the bundled PostgreSQL.

```py
# Example 1: Postgres-backed application
import pgserver

# pgserver-extend is a fork of pgserver, but the Python API is exposed through the
# pgserver module in this codebase.
db = pgserver.get_server(MYPGDATA)
# server ready for connection.

print(db.psql('create extension vector'))
db_uri = db.get_uri()
# use uri with SQLAlchemy / psycopg, etc.

# if no other process is using this server, it will shut down at exit.
# if other processes are using the same PGDATA directory, the server will stay
# alive until the last one exits.
```

```py
# Example 2: Testing
import tempfile
import pytest

@pytest.fixture
def tmp_postgres():
    tmp_pg_data = tempfile.mkdtemp()
    pg = pgserver.get_server(tmp_pg_data, cleanup_mode='stop')
    yield pg
    pg.cleanup()
```

Postgres binaries in the package can be found in the directory pointed to by `pgserver.POSTGRES_BIN_PATH` and used directly.

This project is a fork of `pgserver`, originally based on [](https://github.com/michelp/postgresql-wheel), which provides a Linux wheel. The fork adds the following differences:
1. binary wheels for multiple platforms (Ubuntu x86_64, macOS Apple Silicon, macOS x86_64, Windows)
2. PostgreSQL Python management for cross-platform startup and cleanup, including many edge cases such as Colab and other constrained environments
3. a broader set of bundled extensions, including `pgvector` and several other useful PostgreSQL extensions, while still excluding `postGIS`
