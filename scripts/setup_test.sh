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
    mkdir -p ./tmp
    set -o nounset
    # Install test requirements
    uv pip install --upgrade -e . -r requirements_test.txt -c https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/package_constraints.txt -r https://raw.githubusercontent.com/home-assistant/core/dev/requirements_test.txt -r https://raw.githubusercontent.com/home-assistant/core/dev/requirements_test_pre_commit.txt
    # Prepare biomejs
    echo "Fetching/updating biome cli"
    if uname -a | grep -q arm64; then
      curl -sL "https://github.com/biomejs/biome/releases/latest/download/biome-darwin-arm64" -o "${my_path}/tmp/biome"
    elif uname -a | grep -q x86_64; then
      curl -sL "https://github.com/biomejs/biome/releases/latest/download/biome-linux-x64" -o "${my_path}/tmp/biome"
    else
      echo "Unable to determine processor and as such to install packaged biome cli version, bailing out"
      exit 2
    fi

    # Make biome executable (if necessary)
    chmod +x "${my_path}/tmp/biome"

    # Install pre-commit hook unless running from within pre-commit
    if [ "$#" -eq 0 ]; then
      "${my_venv}/bin/pre-commit" install
    fi
else
    echo "Virtualenv available, bailing out"
    exit 2
fi
