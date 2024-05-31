# Plugwise python module

This module is the backend for the [`plugwise` component](https://github.com/home-assistant/core/tree/dev/homeassistant/components/plugwise) in Home Assistant Core (which we maintain as co-code owners).

This module supports `Smile`s (and `Stretch`), i.e. the networked plugwise devices. For the USB (or Stick-standalone version) please refer to upcoming [`plugwise-usb` component](https://github.com/plugwise/plugwise_usb-beta).

Our main usage for this module is supporting [Home Assistant](https://www.home-assistant.io) / [home-assistant](http://github.com/home-assistant/core/)

[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/plugwise)
[![CodeRabbit.ai is Awesome](https://img.shields.io/badge/AI-orange?label=CodeRabbit&color=orange&link=https%3A%2F%2Fcoderabbit.ai)](https://coderabbit.ai)
[![renovate maintained](https://img.shields.io/badge/maintained%20with-renovate-blue?logo=renovatebot)](https://github.com/plugwise/python-plugwise/issues/291)

[![PyPI version fury.io](https://badge.fury.io/py/plugwise.svg)](https://pypi.python.org/pypi/plugwise/)
[![Latest release](https://github.com/plugwise/python-plugwise/workflows/Latest%20release/badge.svg)](https://github.com/plugwise/python-plugwise/actions)
[![Newest commit](https://github.com/plugwise/python-plugwise/workflows/Latest%20commit/badge.svg)](https://github.com/plugwise/python-plugwise/actions)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/plugwise/python-plugwise/main.svg)](https://results.pre-commit.ci/latest/github/plugwise/python-plugwise/main)

[![CodeFactor](https://www.codefactor.io/repository/github/plugwise/python-plugwise/badge)](https://www.codefactor.io/repository/github/plugwise/python-plugwise)
[![codecov](https://codecov.io/gh/plugwise/python-plugwise/branch/main/graph/badge.svg)](https://codecov.io/gh/plugwise/python-plugwise)

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=plugwise_python-plugwise&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=plugwise_python-plugwise)
[![Technical Debt](https://sonarcloud.io/api/project_badges/measure?project=plugwise_python-plugwise&metric=sqale_index)](https://sonarcloud.io/summary/new_code?id=plugwise_python-plugwise)
[![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=plugwise_python-plugwise&metric=code_smells)](https://sonarcloud.io/summary/new_code?id=plugwise_python-plugwise)

## Integration

### Home-Assistant Integration

(maintained through Home-Assistant)

[![Generic badge](https://img.shields.io/badge/HA%20core-yes-green.svg)](https://github.com/home-assistant/core/tree/dev/homeassistant/components/plugwise)

Works out of the box with every Home Assistant installation, use the button below to install

[![Open your Home Assistant instance and show your integrations.](https://my.home-assistant.io/badges/integrations.svg)](https://my.home-assistant.io/redirect/integrations/)

### Home-Assistant custom_component (beta)

We do (also) maintain a `custom_component`, please note this is **only** intended for users helping us test new features (use at your own risk)

[![Generic badge](https://img.shields.io/github/v/release/plugwise/plugwise-beta)](https://github.com/plugwise/plugwise-beta)

You can add our `custom_component` repository to HACS, do note that we do not intent for our `beta` `custom_component` to be included in the HACS repository.

[![Generic badge](https://img.shields.io/badge/HACS-add%20our%20repo-yellow.svg)](https://github.com/plugwise/plugwise-beta)

See the [`plugwise-beta`](https://github.com/plugwise/plugwise-beta) repository for more info.

## Development/patches

Like Home Assistant Core, we use `pre-commit` and additionally run [pre-commit.ci](http://pre-commit.ci) to automatically validate your commits and PRs.

If you want to create a PR, please ensure you at least run `scripts/setup.sh`. This will ensure your environment is set up correctly before attempting to `git commit`. We sincerely and highly recommended also setting up local testing, see [`tests/README.md`](https://github.com/plugwise/python-plugwise/blob/main/tests/README.md) for more information and run `scripts/setup_test.sh` to prepare your environment.

## Project support status

**Notice** at this time we are refactoring the module code to move towards a supporting way for the integration to become multiple components under an umbrella `plugwise` integration featuring multiple components.

Module providing interfacing with the Plugwise devices:

### Smile

- [x] Adam
  - [x] Lisa
  - [x] Jip
  - [x] Floor
  - [x] Tom
  - [x] Koen (a Koen always comes with a Plug, the Plug is the active part)
  - [x] Plug
  - [x] Aqara Plug
- [x] Anna
- [x] Smile P1
- [x] Stretch
- [ ] Some of the equipment mentioned in USB when in use via Stretch or Adam

- [x] [Home-Assistant](https://home-assistant.io) via
  - [x] Native supporting networked Plugwise products
  - [x] [HACS](https://hacs.xyz) and `custom_component` [Plugwise Beta](https://github.com/plugwise/plugwise-beta/) (supporting all devices above)

## License, origins and contributors

As per the origins, we have retained the appropriate licensing and including the MIT-license for this project.

Origins (from newest to oldest):

- Networked (Smile/Stretch) Plugwise support by @bouwew (Bouwe) and @CoMPaTech (Tom). We both support and help out @brefra (Frank) where possible, he's supporting the USB module and integration.
- 'All' available Plugwise support by @bouwew (Bouwe), @brefra (Frank) and @CoMPaTech (Tom)
- Upstreamed haanna/HA-core Anna, including all later products - 'Plugwise-Smile/Plugwise-HA/plugwise-beta' by @bouwew (Bouwe) & @CoMPaTech (Tom)
- Networked Plugwise Anna module with custom_module - `haanna/anna-ha` via <https://github.com/laetificat> (Kevin)
- USB-based stick module with custom_module - `plugwise-stick/plugwise` by @brefra (Frank)
- USB-plugwise module - `plugwise` by <https://github.com/cyberjunky/python-plugwise> (Ron) originally by <https://github.com/aequitas/python-plugwise> (Johan) (with reference only in license to Sven)
- Sensor for Plugwise Smile P1 integration - `home-assistant-sensor-plugwise-smile-p1` by <https://bitbucket.org/jvdschoot/home-assistant-sensor-plugwise-smile-p1> (Jeroen van der Schoot)

## Thanks

On behalf of all of us, big thanks to Plugwise and community members @riemers and @tane from [HAshop](https://hashop.nl) for their support and obviously all our users and testers who dealt with our typos and challenges. Disclaimer, while we are communicating with Plugwise and they expressed their gratitude through their newsletter, we are not part of Plugwise as a company. We are just a bunch of guys anxious to get our (and your) Plugwise products working with Home Assistant.
