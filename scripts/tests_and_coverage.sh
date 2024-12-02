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

# Install/update dependencies
pre-commit install
pre-commit install-hooks
pip install uv
uv pip install -r requirements_test.txt -r requirements_commit.txt

set +u

if [ -z "${GITHUB_ACTIONS}" ] || [ "$1" == "test_and_coverage" ] ; then
    # Python tests (rerun with debug if failures)
    PYTHONPATH=$(pwd) pytest -qx tests/ --cov='.' --no-cov-on-fail --cov-report term-missing || PYTHONPATH=$(pwd) pytest -xrpP --log-level debug tests/
fi

if [ -z "${GITHUB_ACTIONS}" ] || [ "$1" == "linting" ] ; then
    # Black first to ensure nothings roughing up ruff
    echo "... ruff-ing ..."
    ruff check plugwise/ tests/

    echo "... pylint-ing ..." 
    pylint plugwise/ tests/

    echo "... mypy-ing ..."
    mypy plugwise/
fi

# As to not generated fixtures, leaving biome to re-do them
# so no auto-generation during github run of testing
# Creating todo #313 to 'gracefully' do this on merge on github action
if [ -z "${GITHUB_ACTIONS}" ] || [ "$1" == "fixtures" ] ; then
   echo "... crafting manual fixtures ..." 
   PYTHONPATH=$(pwd) python3 scripts/manual_fixtures.py
fi
echo "... biome-ing (fixtures and testdata) ..." 
./tmp/biome lint --staged --files-ignore-unknown=true --no-errors-on-unmatched
