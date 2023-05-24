#!/bin/bash

set -e

if [ "$EUID" -eq 0 ]; then
    echo "Cannot be root!"
    exit 1
fi

BASE_DIR=$(realpath "$(dirname $0)")
CUSTOM_ROS_MSG_DIR=$1
SOURCES_PATH=${2:-${BASE_DIR}/source_list.json}

GEN_MSG_ROOT=${BASE_DIR}/genmsg

if [ -z ${CUSTOM_ROS_MSG_DIR} ]; then
    echo "Custom messages not specified. Not generating custom messages"
else
    mkdir -p ${GEN_MSG_ROOT}
    ROS_MSG_DIR=${GEN_MSG_ROOT}/${CUSTOM_PKG_NAME}
    rm -r ${ROS_MSG_DIR} || true
    cp -r ${SRC_ROS_MSG_DIR} ${ROS_MSG_DIR}
fi

CUSTOM_PKG_NAME=$(basename ${INTERFACES_BASE_DIR})

source ${BASE_DIR}/venv/bin/activate
python3 ${BASE_DIR}/clone_repos.py ${SOURCES_PATH} ${GEN_MSG_ROOT}
rospy-build genmsg ${ROS_MSG_DIR} -s ${GEN_MSG_ROOT}
python3 -m pip install -e ${ROS_MSG_DIR}
