#!/usr/bin/env bash
set -eu

my_path=$(git rev-parse --show-toplevel)

. ${my_path}/scripts/python-venv.sh

if [ -f "${my_venv}/bin/activate" ]; then
    . "${my_venv}/bin/activate"
    echo "-----------------------------"
    echo "Running cyclomatic complexity"
    echo "-----------------------------"
    PYTHONPATH=$(pwd) radon cc plugwise/smile.py plugwise/helper.py tests/test_smile.py -s -nc --no-assert
else
    echo "Virtualenv available, bailing out"
    exit 2
fi
