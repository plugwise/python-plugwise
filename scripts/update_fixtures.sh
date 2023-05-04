#!/usr/bin/env bash
set -eu

# Fixtures consumed by plugwise-beta
test_fixtures="adam_multiple_devices_per_zone m_adam_cooling m_anna_heatpump_cooling p1v3_full_option stretch_v31 anna_heatpump_heating m_adam_heating m_anna_heatpump_idle p1v4_442_triple"

# If plugwise-beta is relative to this repository, check if files differ and update accordingly
if [ -d ../plugwise-beta ]; then
  for fixture in ${test_fixtures}; do
    echo "Checking fixture ${fixture}: "
    diff -qr "fixtures/${fixture}" "../plugwise-beta/tests/components/plugwise/fixtures/${fixture}" > /dev/null && continue
    echo " - Out-of-date ... updating fixture in plugwise-beta"
    if [ -d "../plugwise-beta/tests/components/plugwise/fixtures/${fixture}" ]; then
      cp -pfr fixtures/"${fixture}"/* ../plugwise-beta/tests/components/plugwise/fixtures/"${fixture}"/
    fi
  done
fi
