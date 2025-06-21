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
arch=$(uname -m)
case "$arch" in
  aarch64|arm64) use_arch="darwin-arm64" ;;
  x86_64)       use_arch="linux-x64" ;;
  *) echo "Unsupported arch for biome cli version: $arch"; exit 2 ;;
esac
curl -sL "https://github.com/biomejs/biome/releases/latest/download/biome-${use_arch}" -o "${my_path}/tmp/biome"

# Make biome executable (if necessary)
chmod +x "${my_path}/tmp/biome"

# Install pre-commit hook unless running from within pre-commit
if [ "$#" -eq 0 ]; then
  pre-commit install
fi
