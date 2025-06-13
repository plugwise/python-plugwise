#!/usr/bin/env bash
# 20250613 Copied from HA-core and shell-check adjusted and modified for local use
set -e

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

# Install commit requirements
uv pip install --upgrade -e . -r requirements_commit.txt -c https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/package_constraints.txt -r https://raw.githubusercontent.com/home-assistant/core/dev/requirements_test_pre_commit.txt

# Install pre-commit hook
pre-commit install
