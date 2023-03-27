#!/usr/bin/env bash
set -eu

my_path=$(git rev-parse --show-toplevel)

# shellcheck disable=SC1091
. "${my_path}/scripts/python-venv.sh"

# shellcheck disable=SC2154
if [ -f "${my_venv}/bin/activate" ]; then
    # shellcheck disable=SC1091
    . "${my_venv}/bin/activate"
    if [ ! "$(which pytest)" ]; then
        echo "Unable to find pytest, run setup_test.sh before this script"
        exit 1
    fi
else
    echo "Virtualenv available, bailing out"
    exit 2
fi

set +u

if [ -z "${GITHUB_ACTIONS}" ] || [ "$1" == "test_and_coverage" ] ; then
    # Python tests (rerun with debug if failures)
    PYTHONPATH=$(pwd) pytest -qx tests/test_smile.py --cov='.' --no-cov-on-fail --cov-report term-missing || PYTHONPATH=$(pwd) pytest -xrpP --log-level debug tests/test_smile.py 
fi

if [ -z "${GITHUB_ACTIONS}" ] || [ "$1" == "linting" ] ; then
    # Black first to ensure nothings roughing up ruff
    echo "... black-ing ..." 
    black plugwise/ tests/

    echo "... ruff-ing ..."
    ruff plugwise/ tests/

    echo "... pylint-ing ..." 
    pylint plugwise/ tests/
fi
