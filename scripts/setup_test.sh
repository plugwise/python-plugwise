#!/usr/bin/env bash
# 20250613 Copied from HA-core and shell-check adjusted and modified for local use
set -e

my_path=$(git rev-parse --show-toplevel)

if [ -z "$VIRTUAL_ENV" ]; then
  if [ -x "$(command -v uv)" ]; then
    uv venv venv
  else
    python3 -m venv venv
  fi
  # shellcheck disable=SC1091 # ingesting virtualenv
  source venv/bin/activate
fi

if ! [ -x "$(command -v uv)" ]; then
  python3 -m pip install uv
fi

mkdir -p ./tmp

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
  pre-commit install
fi
