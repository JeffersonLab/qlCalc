#!/bin/bash

# Get the directory containing this script
DIR="$( cd "$( dirname "$(readlink -f "${BASH_SOURCE[0]}")" )" >/dev/null 2>&1 && pwd )"

# Get the root application directory
APPDIR="$(dirname $DIR)"

# Setup path
export PATH="/usr/csite/pubtools/python/3.6.9/bin:$PATH"

# Setup python search path
OLD_PATH=${PYTHONPATH}
if [ -n $OLD_PATH ] ; then
    export PYTHONPATH="${APPDIR}:${OLD_PATH}"
else
    export PYTHONPATH="${APPDIR}"
fi

python3 "${APPDIR}/app/main.py"
