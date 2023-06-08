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
    # Install commit requirements
    pip install wheel
    pip install --upgrade -e . -r requirements_commit.txt -c https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/package_constraints.txt -r https://raw.githubusercontent.com/home-assistant/core/dev/requirements_test_pre_commit.txt
    # Install pre-commit hook
    "${my_venv}/bin/pre-commit" install
    # Prepare node virtualenv and prettier
    nodeenv -p  # Use node with existing python-virtual env
    npm install prettier
else
    echo "Virtualenv available, bailing out"
    exit 2
fi
