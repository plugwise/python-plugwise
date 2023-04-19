# Testing (for developers)

Plugwise-Smile has to be in working and functioning condition on all circumstances. Hence testing is applied and tested through [Github Actions](https://github.com/plugwise/python-plugwise/actions).

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

Our tests are mainly conducted locally by the contributors and using Github Actions, see the workflows in `.github/workflows`. You can always look up the latest (hopefully successful) build at [python-plugwise Github actions](https://github.com/plugwise/python-plugwise/actions).

If you want to run tests locally, use the provided `scripts/setup_test.sh` to initialize and enable your virtualenv using `source venv/bin/activate`.

Without your virtualenv, run the `scripts/setup_test.sh` script. With that (and your virtualenv enabled) you can run `scripts/tests_and_coverage.sh` or `scripts/complexity.sh` to show areas that need Cyclometic Complexity improving.

## Quality

Code quality is checked (through [Github Actions](https://github.com/plugwise/python-plugwise/actions)) at [CodeFactor](https://www.codefactor.io/repository/github/plugwise/python-plugwise) and [codecov.io](https://app.codecov.io/gh/plugwise/python-plugwise) as depicted by the badges on the [main repository page](https://github.com/plugwise/python-plugwise).
