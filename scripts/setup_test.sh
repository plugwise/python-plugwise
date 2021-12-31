#!/usr/bin/env bash
set -eu

my_path=$(git rev-parse --show-toplevel)

. ${my_path}/scripts/python-venv.sh

if [ -f "${my_venv}/bin/activate" ]; then
    . "${my_venv}/bin/activate"
    # Install test requirements
    pip install --upgrade -r requirements_test.txt -c https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/package_constraints.txt -r https://raw.githubusercontent.com/home-assistant/core/dev/requirements_test.txt -r https://raw.githubusercontent.com/home-assistant/core/dev/requirements_test_pre_commit.txt
    # Install pre-commit hook
    ${my_venv}/bin/pre-commit install
else
    echo "Virtualenv available, bailing out"
    exit 2
fi
