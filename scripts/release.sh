#!/usr/bin/env bash

set -e

if [[ ! -z "$(git status --porcelain)" ]]; then
    echo "UNCLEAN repo! Abort!"
    exit 234
fi

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

read -p "Is this the correct version (bump before release!) [Yy]? " -n 1 -r
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    exit 113
fi

read -p "Did you push your latest changes (including the version bump?) [Yy]? " -n 1 -r
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    exit 114
fi

python3 setup.py sdist bdist_wheel

python3 -m twine check "${sourceDir}/dist/*"

read -p "Does this look ok? [Yy] " -n 1 -r
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    exit 114
fi

python3 -m twine upload --verbose --repository-url https://upload.pypi.org/legacy/ dist/*
git tag -a "v${version}" -m "Release version ${version}"
git push origin "v${version}"
