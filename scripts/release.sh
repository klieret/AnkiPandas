#!/usr/bin/env bash

# This script is used to push a new release to pypy and add an appropriate
# tag to the git repository.

set -e

# Upload to pypi
# Note: Need to bump version first!
# (it's impossible to amend a release, you can only
# make a new release)

thisDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
sourceDir="${thisDir}/.."

oldDir=$(pwd)

function atExit {
    cd "${oldDir}"
}

trap atExit EXIT

cd "${sourceDir}"

rm -rf "dist/"

version=$(cat ankipandas/version.txt)
echo "Version is: " $version

# just to be sure we don't forget to commit it
git add ankipanas/version.txt

python3 setup.py sdist bdist_wheel
python3 -m twine upload --verbose --repository-url https://upload.pypi.org/legacy/ dist/*
git tag -a "v${version}" -m "Release version ${version}"
git push origin "v${version}"

# Cleanup
bash "${thisDir}/clean.sh"
