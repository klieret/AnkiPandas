#!/usr/bin/env bash

# This script will install the hooks to git
# by creating symlinks to the executables in this directory

# https://stackoverflow.com/questions/59895/
thisDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

gitDir="${thisDir}/../.git"
gitHookDir="${gitDir}/hooks"

for file in pre-commit
do
	if [[ ! -f "${gitHookDir}/${file}" ]]; then
	    echo "Linking to \"${file}\""
		ln -s ${thisDir}/${file} ${gitHookDir}/${file}
	else
	    echo "Hook \"${file}\" already exists. Skip."
	fi
done
