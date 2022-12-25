#!/usr/bin/env sh

# Used to find dependencies not strictly set
# Use-case:
#   - We used to have our own package_constraints.txt to handle upstream HA-core dependencies (but never amended it)
#   - We have a couple of local 'commit' and 'test' requirements in common (e.g. we let HA-core prevail)
#   - For everything *not* in use by HA-core we still would want dependabot to kick in appropriately
#   - This script will exit with error if it finds 'unversioned' dependencies (as such should be part of our CI)

# Use local tmp
if [ ! -d ./tmp ]; then
  mkdir -p ./tmp/urls
fi

# Find URLs used
urls=$(grep -hEo "(http|https)://[a-zA-Z0-9./?=_%:-]*" ./scripts/setup*.sh | sort -u)

# Cache upstream information
i=1
for url in ${urls}; do
  curl -s "${url}" > ./tmp/urls/${i}
  i=$((i+1))
done

# Find local packages
packages=$(grep -hEv "^$|^#|^\-e" ./requirements*.txt | cut -f 1 -d '=' | sort -u)

# Check for local defined packages against upstream
pkglist="./tmp/pkglist"
true > "${pkglist}"
for pkg in ${packages}; do
  # shellcheck disable=SC2046,SC2143
  if [ ! $(grep -rhE "^${pkg}" ./tmp/urls) ]; then
#    echo "${pkg} not in upstream requirements/constraints"
    echo "${pkg}" >> "${pkglist}"
  fi
done

# Check for versioning in local packages
pkgmiss="./tmp/pkglist.miss"
true > "${pkgmiss}"
# shellcheck disable=SC2013
for pkg in $(sort -u ${pkglist}); do
  # shellcheck disable=SC2046,SC2143
  if [ ! $(grep -rhE "^${pkg}==" ./requirements*.txt) ]; then
#    echo "${pkg} no versioning defined"
    echo "${pkg}" >> "${pkgmiss}"
  fi
done

# Print missing information and exit error out
# shellcheck disable=SC2046
if [ $(wc -l "${pkgmiss}" | awk '{print $1}') -gt 0 ]; then
  echo "Packages missing from local requirements_*.txt files:"
  # shellcheck disable=SC2013
  for pkg in $(sort -u ${pkgmiss}); do
    echo "  ${pkg} in $(grep -hlE "^${pkg}" ./requirements*.txt) missing version information"
  done
  exit 1
fi
