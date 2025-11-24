#!/usr/bin/env bash
# 20250613 Copied from HA-Core: run-in-env.sh
set -eu

# Used in venv activate script.
# Would be an error if undefined.
OSTYPE="${OSTYPE-}"

# Activate pyenv and virtualenv if present, then run the specified command

# pyenv, pyenv-virtualenv
if [ -s .python-version ]; then
    PYENV_VERSION=$(head -n 1 .python-version)
    export PYENV_VERSION
fi

if [ -n "${VIRTUAL_ENV-}" ] && [ -f "${VIRTUAL_ENV}/bin/activate" ]; then
  # shellcheck disable=SC1091 # ingesting virtualenv
  . "${VIRTUAL_ENV}/bin/activate"
else
  # other common virtualenvs
  my_path=$(git rev-parse --show-toplevel)

  for venv in venv .venv .; do
    if [ -f "${my_path}/${venv}/bin/activate" ]; then
      # shellcheck disable=SC1090 # ingesting virtualenv
      . "${my_path}/${venv}/bin/activate"
      break
    fi
  done
fi

# 20250613 End of copy

if ! command -v pytest >/dev/null; then
  echo "Unable to find pytest, run setup_test.sh before this script"
  exit 1
fi

handle_command_error() {
    if [ $? -ne 0 ]; then
        echo "Error: $1 failed"
        exit 1
    fi
}

biome_format() {
    ./tmp/biome check fixtures/ plugwise/ tests/ --files-ignore-unknown=true --no-errors-on-unmatched --indent-width=2 --indent-style=space --write
    handle_command_error "biome formatting"
}

# Install/update dependencies
pre-commit install
pre-commit install-hooks
uv pip install -r requirements_test.txt -r requirements_commit.txt

set +u

if [ -z "${GITHUB_ACTIONS}" ] || [ "$1" == "test_and_coverage" ] ; then
    # Python tests (rerun with debug if failures)
    # PYTHONPATH=$(pwd) pytest -qx tests/ --cov='.' --no-cov-on-fail --cov-report term-missing || 
    PYTHONPATH=$(pwd) pytest -xrpP --log-level debug tests/
    handle_command_error "python code testing"
fi

if [ -z "${GITHUB_ACTIONS}" ] || [ "$1" == "linting" ] ; then
    echo "... biome-ing (prettier) ..."
    biome_format

    echo "... ruff checking ..."
    ruff check plugwise/ tests/
    handle_command_error "ruff checking"
    echo "... ruff formatting ..."
    ruff format plugwise/ tests/
    handle_command_error "ruff formatting"

    echo "... pylint-ing ..." 
    pylint plugwise/ tests/
    handle_command_error "pylint validation"

    echo "... mypy-ing ..."
    mypy plugwise/
    handle_command_error "mypy validation"
fi

# As to not generated fixtures, leaving biome to re-do them
# so no auto-generation during github run of testing
# Creating todo #313 to 'gracefully' do this on merge on github action
if [ -z "${GITHUB_ACTIONS}" ] || [ "$1" == "fixtures" ] ; then
   echo "... Crafting manual fixtures ..." 
   PYTHONPATH=$(pwd) python3 scripts/manual_fixtures.py
    echo "... (re) biome-ing (prettier) ..."
    biome_format
fi
