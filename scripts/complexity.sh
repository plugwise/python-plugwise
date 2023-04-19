#!/usr/bin/env bash
set -eu

my_path=$(git rev-parse --show-toplevel)

# shellcheck disable=SC1091
source "${my_path}/scripts/python-venv.sh"

# shellcheck disable=SC2154
if [ -f "${my_venv}/bin/activate" ]; then
    # shellcheck disable=SC1091
    . "${my_venv}/bin/activate"
    echo "-----------------------------"
    echo "Running cyclomatic complexity"
    echo "-----------------------------"
    PYTHONPATH=$(pwd) radon cc plugwise/ tests/ -s -nc --no-assert
else
    echo "Virtualenv available, bailing out"
    exit 2
fi
