#!/bin/bash

set -e

if [ "$EUID" -eq 0 ]; then
    echo "Cannot be root!"
    exit 1
fi

BASE_DIR=$(realpath "$(dirname $0)")
SOURCES_PATH=${1:-${BASE_DIR}/source_list.json}
GEN_MSG_ROOT=${BASE_DIR}/genmsg
source ${BASE_DIR}/venv/bin/activate
python3 ${BASE_DIR}/clone_repos.py ${SOURCES_PATH} ${GEN_MSG_ROOT}
python3 ${BASE_DIR}/generate_messages.py ${SOURCES_PATH} ${GEN_MSG_ROOT}
