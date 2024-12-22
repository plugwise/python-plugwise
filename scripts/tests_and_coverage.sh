#!/usr/bin/env bash
set -eu

my_path=$(git rev-parse --show-toplevel)

# shellcheck disable=SC1091
. "${my_path}/scripts/python-venv.sh"

# shellcheck disable=SC2154
if [ -f "${my_venv}/bin/activate" ]; then
    set +o nounset  # Workaround https://github.com/pypa/virtualenv/issues/150 for nodeenv
    # shellcheck disable=SC1091
    . "${my_venv}/bin/activate"
    set -o nounset
    if [ ! "$(which pytest)" ]; then
        echo "Unable to find pytest, run setup_test.sh before this script"
        exit 1
    fi
else
    echo "Virtualenv available, bailing out"
    exit 2
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
pip install uv
uv pip install -r requirements_test.txt -r requirements_commit.txt

set +u

if [ -z "${GITHUB_ACTIONS}" ] || [ "$1" == "test_and_coverage" ] ; then
    # Python tests (rerun with debug if failures)
    PYTHONPATH=$(pwd) pytest -qx tests/ --cov='.' --no-cov-on-fail --cov-report term-missing || PYTHONPATH=$(pwd) pytest -xrpP --log-level debug tests/
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
