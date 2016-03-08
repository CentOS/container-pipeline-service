#!/usr/bin/bash

ADMIN="--config=/var/lib/origin/openshift.local.config/master/admin.kubeconfig"


function usage() {
    echo "`basename $0` NAME REPO_URL"
    echo "   NAME      Name of the project/namespace"
    echo "   TAG       Name of the resulting image (image will be named NAME/TAG:latest)"
    echo "   REPO_URL  URL of project repository containing Dockerfile"
    exit 0
}

function _oc() {
    oc $@
}

NAME=$1
TAG=$2
REPO=$3

[ "${NAME}" == "" ] || [ "${NAME}" == "-h" ] || [ "${NAME}" == "--help" ] && usage
[ "${TAG}" == "" ] && usage
[ "${REPO}" == "" ] && usage


CWD=`dirname $0`
NS="--namespace ${NAME}"

_oc new-project ${NAME} --display-name=${NAME}
_oc ${NS} create -f ${CWD}/template.json
_oc ${NS} process cccp-demo -v SOURCE_REPOSITORY_URL=${REPO},TARGET_NAMESPACE=${NAME},TAG=${TAG} | oc create -f -


IP=$(ip -f inet addr show eth1 2> /dev/null | grep 'inet' | awk '{ print $2}' | sed 's#/.*##')

BUILD=$(_oc ${NS} start-build build)



[ $? -eq 0 ] && echo -e "Build ${BUILD} started.\nYou can watch builds progress at https://${IP}:8443/console/project/${NAME}/browse/builds"
