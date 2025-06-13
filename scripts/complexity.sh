#!/usr/bin/env bash
set -eu

my_path=$(git rev-parse --show-toplevel)

if [ -n "${VIRTUAL_ENV-}" ] && [ -f "${VIRTUAL_ENV}/bin/activate" ]; then
  # shellcheck disable=SC1091 # ingesting virtualenv
  . "${VIRTUAL_ENV}/bin/activate"
else
  # other common virtualenvs
  my_path=$(git rev-parse --show-toplevel)

  for venv in venv .venv .; do
    if [ -f "${my_path}/${venv}/bin/activate" ]; then
      # shellcheck disable=SC1090 # ingesting virtualenv
      . "${my_path}/${venv}/bin/activate"
      break
    fi
  done
fi

echo "-----------------------------"
echo "Running cyclomatic complexity"
echo "-----------------------------"
PYTHONPATH=$(pwd) radon cc plugwise/ tests/ -s -nc --no-assert
