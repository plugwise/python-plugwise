# Setups included for testing (help us out!)

Below you'll find a list of setups we have (green) and are still looking for (yellow). If you are willing to help out the community, please share your setup with us. Below the list you'll find a paragraph detailing how you can best submit your data without everybody on the Internet being able to control your precious Smile.

## Setups

Intended: (yellow ones means, please submit yours)

 - [![Generic badge](https://img.shields.io/badge/Adam-v3-yellow.svg)]() setup with a boiler, Floor, Koen, Plug, Tom and Lisa (i.e. the whole shebang) (`adam_full_option`)
 - [![Generic badge](https://img.shields.io/badge/Adam-v3-green.svg)](https://github.com/plugwise/Plugwise-Smile/tree/docs/tests/adam_living_floor_plus_3_rooms) setup with a boiler, Floor, Lisa and 3x Toms (riemers)
 - [![Generic badge](https://img.shields.io/badge/Adam-v3-green.svg)](https://github.com/plugwise/Plugwise-Smile/tree/docs/tests/adam_multiple_devices_per_zone) setup with everything but Koen and Anna, multiple devices per zone (tane)
 - [![Generic badge](https://img.shields.io/badge/Adam-v3-green.svg)](https://github.com/plugwise/Plugwise-Smile/tree/docs/tests/adam_zone_per_device) setup with everything but Koen and Anna, device per zone (tane)
 - [![Generic badge](https://img.shields.io/badge/Adam-v3-yellow.svg)]() setup without a boiler, but with Lisa and either a Plug or a Tom (`adam_without_boiler`) 

 - [![Generic badge](https://img.shields.io/badge/Adam_Anna-v3-green.svg)](https://github.com/plugwise/Plugwise-Smile/tree/docs/tests/adam_plus_anna) a boiler, Adam, Anna and Tom (bouwew)

 - [![Generic badge](https://img.shields.io/badge/Anna-v4-green.svg)](https://github.com/plugwise/Plugwise-Smile/tree/docs/tests/anna_v4) setup with a boiler ()
 - [![Generic badge](https://img.shields.io/badge/Anna-v3-green.svg)](https://github.com/plugwise/Plugwise-Smile/tree/docs/tests/anna_without_boiler_fw3) without boiler(i.e. attached to city heating) (compatech)
 - [![Generic badge](https://img.shields.io/badge/Anna-v4-green.svg)](https://github.com/plugwise/Plugwise-Smile/tree/docs/tests/anna_without_boiler_fw4) without boiler(i.e. attached to city heating) (compatech)
 - [![Generic badge](https://img.shields.io/badge/Anna-v1-green.svg)](https://github.com/plugwise/Plugwise-Smile/tree/docs/tests/legacy_anna) setup with a boiler, but legacy firmware (1.8) ()
 - [![Generic badge](https://img.shields.io/badge/Anna-v1-green.svg)](https://github.com/plugwise/Plugwise-Smile/tree/docs/tests/legacy_anna_2) another setup with a boiler, but legacy firmware (1.8), but with a location ()

 - [![Generic badge](https://img.shields.io/badge/P1-v3-green.svg)](https://github.com/plugwise/Plugwise-Smile/tree/docs/tests/p1v3) electricity only (compatech)
 - [![Generic badge](https://img.shields.io/badge/P1-v3-green.svg)](https://github.com/plugwise/Plugwise-Smile/tree/docs/tests/p1v3solarfake) electricity only - just the above with added data, please submit **yours** (from above)
 - [![Generic badge](https://img.shields.io/badge/P1-v3-green.svg)](https://github.com/plugwise/Plugwise-Smile/tree/docs/tests/p1v3_full_option) electricity, solar and gas ()
 - [![Generic badge](https://img.shields.io/badge/P1-v3-yellow.svg)]() electricity and gas (`p1v3_gas_nosolar`)
 - [![Generic badge](https://img.shields.io/badge/P1-v2-green.svg)](https://github.com/plugwise/Plugwise-Smile/tree/docs/tests/smile_p1_v2) electricity and gas ()
 - [![Generic badge](https://img.shields.io/badge/P1-v2-green.svg)](https://github.com/plugwise/Plugwise-Smile/tree/docs/tests/smile_p1_v2_2) another electricity and gas ()

## Sharing

If you see a yellow item and feel your setup fits in, please **MAIL** one of the authors the output of the below links. Feel free to create a PR if you follow the below privacy hint:

They should al start with `<xml` and copied as plain text (i.e. not preformatted like Chrome and Safari do).
Either use wget/curl or use your 'developer view' from your browser to copy the source text
 
```
http://{ip_of_your_smile}/core/appliances
http://{ip_of_your_smile}/core/direct_objects
http://{ip_of_your_smile}/core/domain_objects
http://{ip_of_your_smile}/core/locations
http://{ip_of_your_smile}/core/modules
```

## Important

Don't commit test-data in `tests` that shouldn't be available to 'the internet'.
To prevent this we've included a pre-commit hook that checks and validates that no private information is there (but do double-check yourselves!)
See 'pre-commit.sh' for details

Excerpt:

 - [ ] modify `domain_objects` and `modules` and set all occurances of `mac-address` to `0123456789AB`
 - [ ] modify `domain_objects` and set `short_id` to `abcdefgh`
 - [ ] modify `domain_objects` and set `wifi_ip` to `127.0.0.1`
 - [ ] modify `domain_objects` and set `lan_ip` to `127.0.0.1`
 - [ ] modify `domain_objects` and set all `ip_addresses` to `127.0.0.1`
 - [ ] modify `domain_objects` and set `hostname` to `smile000000`
 - [ ] modify `domain_objects` and set `longitude` to `4.49`
 - [ ] modify `domain_objects` and set `latitude` to `52.21`
 - [ ] modify `domain_objects` and set `city` to `Sassenheim`
 - [ ] modify `domain_objects` and set `postal_code` to `2171`

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

Now install the requirements into your virtual environment by running `pip install -r requirements.txt -r tests/requirements.txt`. **Note** that you'll have to run the `source venv/bin/activate` each time you work on files to ensure you have the virtual environment.

Now you can test using `./run_tests_and_coverage.sh` from the main directory and watch the results.

