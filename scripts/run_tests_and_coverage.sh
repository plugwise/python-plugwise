#!/bin/sh
echo "-----------------------------------------------------------"
echo "Running plugwise/smile.py through pytest including coverage"
echo "-----------------------------------------------------------"
PYTHONPATH=`pwd` pytest -rpP --log-level debug tests/test_smile.py --cov='.' --no-cov-on-fail
pytest=`echo $?`
echo "-----------------------------------------------------------------"
echo "pytest exit code: ${pytest}"
echo "-----------------------------------------------------------------"
