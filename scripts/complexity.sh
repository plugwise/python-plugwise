#!/bin/bash
echo "-----------------------------"
echo "Running cyclomatic complexity"
echo "-----------------------------"
PYTHONPATH=$(pwd) radon cc plugwise/smile.py plugwise/helper.py tests/test_smile.py -s -nc --no-assert
