#!/usr/bin/env bash
set -eu

# Activate pyenv and virtualenv if present, then run the specified command

# pyenv, pyenv-virtualenv
if [ -s .python-version ]; then
    PYENV_VERSION=$(head -n 1 .python-version)
    export PYENV_VERSION
fi

# other common virtualenvs
my_path=$(git rev-parse --show-toplevel)

for venv in venv .venv .; do
  if [ -f "${my_path}/${venv}/bin/activate" ]; then
    . "${my_path}/${venv}/bin/activate"
    echo "-----------------------------------------------------------"
    echo "Running plugwise/smile.py through pytest including coverage"
    echo "-----------------------------------------------------------"
    PYTHONPATH=$(pwd) pytest -rpP --log-level debug tests/test_smile.py --cov='.' --no-cov-on-fail --cov-report term-missing
    break
  fi
done


