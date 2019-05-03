#!/usr/bin/env bash

# This script removes temporary files from the installation.

set -e

thisDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
mainDir="${thisDir}/.."

/bin/rm -rf "${mainDir}/dist"
/bin/rm -rf "${mainDir}/build"
/bin/rm -rf "${mainDir}/ankipandas.egg-info"
