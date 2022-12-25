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
pkgredundant="./tmp/pkgredundant"
true > "${pkglist}"
true > "${pkgredundant}"
for pkg in ${packages}; do
  # shellcheck disable=SC2046,SC2143
  if [ ! $(grep -rhE "^${pkg}" ./tmp/urls) ]; then
#    echo "${pkg} not in upstream requirements/constraints"
    echo "${pkg}" >> "${pkglist}"
  else
    echo "${pkg}" >> "${pkgredundant}"
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

# Check for versioning in setup.py
pkgpy=$(sed -n '/install_requires=\[/,/\]/p' setup.py | tr -d '\n' | sed 's/^.*\[\(.*\)\].*$/\1/g' | tr -d ',"')
for pkgfull in ${pkgpy}; do
  # Very ugly multi-character split
  # shellcheck disable=SC3011
  pkg=$(echo "${pkgfull}" | cut -d '=' -f 1 | cut -d '<' -f 1 | cut -d '>' -f 1)
  # shellcheck disable=SC2046,SC2143
  if [ ! $(grep -qrhE "^${pkg}" ./tmp/urls) ]; then
#    echo "DEBUG:   ${pkg} from setup.py not in upstream requirements/constraints"
    if [ ! $(grep -rhE "^${pkg}==" ./requirements*.txt) ]; then
#      echo "DEBUG:   ${pkg} from setup.py not in local requirements"
      # shellcheck disable=SC3014
      if [ "${pkg}" = "${pkgfull}" ]; then
        echo "WARNING: ${pkg} not in any requirements and no version specified in setup.py"
#      else
#        echo "DEBUG:   ${pkg} version specified in setup.py"
      fi
#    else
#      echo "DEBUG:   ${pkg} found in local requirements"
    fi
#  else
#    echo "DEBUG:   ${pkg} found in upstream URLs"
  fi
done
echo ""

# Print redundant information (no error value)
# shellcheck disable=SC2046
#if [ $(wc -l "${pkgmiss}" | awk '{print $1}') -gt 0 ]; then
  echo "INFO:    Packages redundant with upstream:"
  # shellcheck disable=SC2013
  for pkg in $(sort -u ${pkgredundant}); do
    echo "INFO:      ${pkg} in ($(grep -hlE "^${pkg}" ./requirements*.txt)) already available via upstream"
  done
  echo ""
#fi

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
