#!/usr/bin/bash

CWD=`dirname $0`
NAMESPACE=$1
GIT_PATH=$2
DOCKERFILE=$3
NOTIFY_EMAIL=$4
JOB_NAME=$5
LOGS_DIR=$6

python $CWD/trigger_dockerfile_lint.py $NAMESPACE $GIT_PATH $DOCKERFILE $NOTIFY_EMAIL $JOB_NAME $LOGS_DIR