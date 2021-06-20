# Plugwise python module

This module is the backend for the [`plugwise` component](https://github.com/home-assistant/core/tree/dev/homeassistant/components/plugwise) which we maintain in Home Assistant Core.

Our main usage for this module is supporting [Home Assistant](https://www.home-assistant.io) / [home-assistant](http://github.com/home-assistant/core/)

[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/plugwise)
[![CodeFactor](https://www.codefactor.io/repository/github/plugwise/python-plugwise/badge)](https://www.codefactor.io/repository/github/plugwise/python-plugwise)
[![Latest release](https://github.com/plugwise/python-plugwise/workflows/Latest%20release/badge.svg)](https://github.com/plugwise/python-plugwise/actions)
[![codecov](https://codecov.io/gh/plugwise/python-plugwise/branch/main/graph/badge.svg)](https://codecov.io/gh/plugwise/python-plugwise)
[![PyPI version fury.io](https://badge.fury.io/py/plugwise.svg)](https://pypi.python.org/pypi/plugwise/)
[![Newest commit](https://github.com/plugwise/python-plugwise/workflows/Latest%20commit/badge.svg)](https://github.com/plugwise/python-plugwise/actions)

## Integration

### Home-Assistant Integration

(maintained through Home-Assistant)

[![Generic badge](https://img.shields.io/badge/HA%20core-yes-green.svg)](https://github.com/home-assistant/core/tree/dev/homeassistant/components/plugwise)

Works out of the box with every Home Assistant installation

### Home-Assistant custom_component (beta)

Intended for users helping us test new features (use at your own risk)

[![Generic badge](https://img.shields.io/github/v/release/plugwise/plugwise-beta)](https://github.com/plugwise/plugwise-beta)
[![Generic badge](https://img.shields.io/badge/HA%20custom_component-yes-green.svg)](https://github.com/plugwise/plugwise-beta)
[![Generic badge](https://img.shields.io/badge/HACS-add%20our%20repo-yellow.svg)](https://github.com/plugwise/plugwise-beta)

See the [`plugwise-beta`](https://github.com/plugwise/plugwise-beta) repository for more info. Requires additional configuration/handling to get your integration running.

## Development/patches

Like Home Assistant Core we use `pre-commit` to validate your commits and eventually PRs.

Please make sure you at least ran `scripts/setup.sh` before attempting to `git commit`. But we sincerely recommended to also use local testing, see `tests/README.md` for more information.

## Project support status

Module providing interfacing with the Plugwise devices:

- [x] Adam
  - [x] Lisa
  - [x] Jip
  - [x] Floor
  - [x] Tom
  - [x] Koen (a Koen always comes with a Plug, the Plug is the active part)
  - [x] Plug
- [x] Anna
- [x] Smile P1
- [x] Stick
  - [x] Circle+ / Stealth+
  - [x] Circle / Stealth
  - [x] Scan
  The devices listed below have **NOT** been tested and are therefore unknown for their correct operation
    - [x] Sense
    - [x] Switch
- [x] Stretch
- [x] [Home-Assistant](https://home-assistant.io) via
  - [x] Native supporting networked Plugwise products
  - [ ] Native supporting USB Plugwise products (in progress)
  - [x] [HACS](https://hacs.xyz) and `custom_component` [Plugwise-HA](https://github.com/plugwise/plugwise-beta/) (supporting all devices above)

## License, origins and contributors

As per the origins we have retained the appropriate licensing and including the MIT-license for this project.

Origins (from newest to oldest):

- 'All' available Plugwise support by @bouwew (Bouwe), @brefra (Frank) and @CoMPaTech (Tom)
- Upstreamed haanna/HA-core Anna, including all later products - 'Plugwise-Smile/Plugwise-HA/plugwise-beta` by @bouwew (Bouwe) & @CoMPaTech (Tom)
- Networked Plugwise Anna module with custom_module - `haanna/anna-ha` via <https://github.com/laetificat> (Kevin)
- USB-based stick module with custom_module - `plugwise-stick/plugwise` by @brefra (Frank)
- USB-plugwise module - `plugwise` by <https://github.com/cyberjunky/python-plugwise> (Ron) originally by <https://github.com/aequitas/python-plugwise> (Johan) (with reference only in license to Sven)

## Thanks

On behalf all of us, big thanks to Plugwise and community members @riemers and @tane from [HAshop](https://hashop.nl)for their support and obviously all our users and testers who dealt with our typos and challenges. Disclaimer, while we are communicating with Plugwise and they expressed their gratitude through their newsletter, we are not part of Plugwise as a company. We are just a bunch of guys anxious to get our (and your) Plugwise products working with Home Assistant.
