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
    echo "-----------------------------------------------------------"
    echo "Running plugwise/smile.py through pytest including coverage"
    echo "-----------------------------------------------------------"
    PYTHONPATH=$(pwd) pytest -rpP --log-level debug tests/test_smile.py --cov='.' --no-cov-on-fail --cov-report term-missing && echo "... flake8-ing ..." && flake8 plugwise/ tests/ && echo "... pylint-ing ..." && pylint plugwise/ tests/ && echo "... black-ing ..." && black plugwise/ tests/
else
    echo "Virtualenv available, bailing out"
    exit 2
fi
