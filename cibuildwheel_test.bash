#! /bin/bash
# Run by cibuildwheel inside each wheel build. Any failure must fail the build:
#  -x stops at the first failing test, the exit code of pytest is propagated.
set -euo pipefail
PROJECT=$1

echo "Running on OSTYPE=$OSTYPE with UID=$UID"

pytest -x -v -ra --tb=short -o log_cli=true --log-cli-level=WARNING "$PROJECT/tests"
