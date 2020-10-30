# Testing (for developers)

Plugwise-Smile has to be in working and functioning condition on all circumstances. Hence testing.

## Tests
From the above list of setups a number of values is selected to be asserted. Currently we have the following asserts in place:

Information gathering: (negative)

- Check handling against a Smile that 'times out' during request
- Check handling against a Smile refusing contact (`internal server error`)

Service handling (i.e. changing setpoint or switching a relay)

- Check against a Smile not accepting change (`internal server error`) (negative)
- Switch a relay, change a setpoint or change a schema/preset (positive)

Data processing (positive)
- Includes checking various `measures` and settings for each device / location / combination of both

## Running tests against Plugwise Smile

Our tests are mainly conducted locally by the contributors and Travis CI. You can always look up the latest (hopefully successful) build at (Travis for Plugwise-Smile)[https://travis-ci.org/github/plugwise/Plugwise-Smile].


Ensure you have python(3) with virtualenv installed. For ubuntu based systems `apt install python3-pip python3-dev python3-venv`

From the main directory of this repository run `python3 -m venv venv` followed by `source venv/bin/activate`. 

Now install the requirements into your virtual environment by running `scripts/setup_test.sh`. **Note** that you'll have to run the `source venv/bin/activate` each time you work on files to ensure you have the virtual environment.

Now you can test using `scripts/tests_and_coverage.sh` from the main directory and watch the results.

