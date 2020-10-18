#!/bin/sh
echo "-----------------------------------------------------------"
echo "Running plugwise/smile.py through pytest including coverage"
echo "-----------------------------------------------------------"
PYTHONPATH=`pwd` pytest -rpP --log-level debug tests/test_smile.py --cov='.' --no-cov-on-fail
pytest=`echo $?`
echo "-----------------------------------------------------------------"
echo "Running plugwise/smile.py through flake8"
echo "-----------------------------------------------------------------"
PYTHONPATH=`pwd` flake8 --config=.flake8 plugwise/*.py tests/*py
flake8=`echo $?`
echo "-----------------------------------------------------------------"
echo "Running plugwise/smile.py through pydocstyle"
echo "-----------------------------------------------------------------"
PYTHONPATH=`pwd` pydocstyle plugwise/*.py tests/*py
pydocs=`echo $?`
echo "-----------------------------------------------------------------"
echo "Running plugwise/smile.py through pylint (HA-core + own disables)"
echo "-----------------------------------------------------------------"
PYTHONPATH=`pwd` pylint --rcfile=pylintrc plugwise/*.py
pylint=`echo $?`
echo "-----------------------------------------------------------------"
echo "pytest exit code: ${pytest}"
echo "flake8 exit code: ${flake8}"
echo "pydocs exit code: ${pydocs}"
echo "pylint exit code: ${pylint}"
echo "-----------------------------------------------------------------"
