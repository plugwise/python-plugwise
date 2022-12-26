#!/usr/bin/env sh

# Used to find dependencies not strictly set
# Use-case:
#   - We used to have our own package_constraints.txt to handle upstream HA-core dependencies (but never amended it)
#   - We have a couple of local 'commit' and 'test' requirements in common (e.g. we let HA-core prevail)
#   - For everything *not* in use by HA-core we still would want dependabot to kick in appropriately
#   - This script will exit with error if it finds 'unversioned' dependencies (as such should be part of our CI)

# Default to non-error
exitcode=0

# Use local tmp
if [ ! -d ./tmp ]; then
  mkdir -p ./tmp/urls
fi

# Debugging
DEBUG=1
if [ "${1}" = "debug" ]; then DEBUG=0; fi

# Simple debugging trigger
debug_output () {
  if [ ${DEBUG} -eq 0 ]; then echo "DEBUG:   ${1}"; fi
}

debug_output "Finding URLs used for setup"
urls=$(grep -hEo "(http|https)://[a-zA-Z0-9./?=_%:-]*" ./scripts/setup*.sh | sort -u)

debug_output "Caching upstream information"
i=1
for url in ${urls}; do
  curl -s "${url}" > ./tmp/urls/${i}
  i=$((i+1))
done

debug_output "Find local package requirements"
packages=$(grep -hEv "^$|^#|^\-e" ./requirements*.txt | cut -f 1 -d '=' | sort -u)

debug_output "Check local defined packages against upstream"
pkglist="./tmp/pkglist"
pkgredundant="./tmp/pkgredundant"
true > "${pkglist}"
true > "${pkgredundant}"
for pkg in ${packages}; do
  # shellcheck disable=SC2046,SC2143
  if [ ! $(grep -rhE "^${pkg}$|${pkg}[=,.]" ./tmp/urls) ]; then
    debug_output "${pkg} not in upstream requirements/constraints"
    echo "${pkg}" >> "${pkglist}"
  else
    debug_output "${pkg} redundant through upstream requirements/constraints as $(grep -rhE "^${pkg}$|${pkg}[=<>]" ./tmp/urls)"
    echo "${pkg}" >> "${pkgredundant}"
  fi
done

debug_output "Check for versioning in local packages"
pkgmiss="./tmp/pkglist.miss"
true > "${pkgmiss}"
# shellcheck disable=SC2013
for pkg in $(sort -u ${pkglist}); do
  # shellcheck disable=SC2046,SC2143
  if [ ! $(grep -rhE "^${pkg}$|${pkg}[=<>]" ./requirements*.txt) ]; then
    debug_output "${pkg} no versioning defined"
    echo "${pkg}" >> "${pkgmiss}"
  else
    debug_output "${pkg} version locally defined in $(grep -rhE "^${pkg}$|${pkg}[=<>]" ./requirements*.txt)"
  fi
done

debug_output "Check for versioning in setup.py"
pkgpy=$(sed -n '/install_requires=\[/,/\]/p' setup.py | tr -d '\n' | sed 's/^.*\[\(.*\)\].*$/\1/g' | tr -d ',"')
for pkgfull in ${pkgpy}; do
  # Very ugly multi-character split
  # shellcheck disable=SC3011
  pkg=$(echo "${pkgfull}" | cut -d '=' -f 1 | cut -d '<' -f 1 | cut -d '>' -f 1)
  # Check for package in upstream
  # shellcheck disable=SC2046,SC2143
  if [ ! $(grep -rhE "^${pkg}$|^${pkg}[=<>]+" ./tmp/urls) ]; then
    debug_output "${pkg} from setup.py not in upstream requirements/constraints"
    # Check for package locally
    if [ ! $(grep -rhE "^${pkg}$|${pkg}[=<>]" ./requirements*.txt) ]; then
      debug_output "${pkg} from setup.py not in local requirements"
      # shellcheck disable=SC3014
      if [ "${pkg}" = "${pkgfull}" ]; then
        echo "WARNING: ${pkg} not in any requirements and no version specified in setup.py"
      else
        debug_output "${pkg} version specified in setup.py as ${pkgfull}"
      fi
    else
      debug_output "${pkg} found in local requirements as $(grep -rhE "^${pkg}$|${pkg}[=<>]" ./requirements*.txt)"
    fi
  else
    debug_output "${pkg} found in upstream URLs as $(grep -rhE "^${pkg}$|^${pkg}[=<>]+" ./tmp/urls)"
  fi
done
echo ""

# Print missing information and exit error out
# shellcheck disable=SC2046
if [ $(wc -l "${pkgmiss}" | awk '{print $1}') -gt 0 ]; then
  echo "ERROR:  Packages missing from local requirements_*.txt files:"
  # shellcheck disable=SC2013
  for pkg in $(sort -u ${pkgmiss}); do
    echo "INFO:     ${pkg} in $(grep -hlE "^${pkg}" ./requirements*.txt) missing version information"
  done
  echo ""
  exitcode=1
fi

exit ${exitcode}
