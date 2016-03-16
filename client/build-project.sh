#!/usr/bin/bash

ADMIN="--config=/var/lib/origin/openshift.local.config/master/admin.kubeconfig"


function usage() {
    echo "`basename $0` NAME REPO_URL"
    echo "   NAME      Name of the project/namespace"
    echo "   TAG       Name of the resulting image (image will be named NAME/TAG:latest)"
    echo "   REPO_URL  URL of project repository containing Dockerfile"
    echo "   REPO_BUILD_PATH  Relative path to the Dockerfile in the repository"
    exit 0
}

function _oc() {
    oc $@
}

NAME=$1
TAG=$2
REPO=$3
REPO_BUILD_PATH=$4

[ "${NAME}" == "" ] || [ "${NAME}" == "-h" ] || [ "${NAME}" == "--help" ] && usage
[ "${TAG}" == "" ] && usage
[ "${REPO}" == "" ] && usage
[ "${REPO_BUILD_PATH}" == "" ] && usage


CWD=`dirname $0`
NS="--namespace ${NAME}"
echo "==> login to Openshift server"
oc login https://172.29.32.42:8443 -u test-admin -p test --certificate-authority=./ca.crt

echo "==>creating new project"
oc new-project ${NAME} --display-name=${NAME}

echo "==> Uploading template to OpenShift"
for t in $(echo "build bc is"); do
  _oc ${NS} delete $t $(oc get $t -l template=cccp-service --no-headers | awk '{print $1}')
done
_oc ${NS} get --no-headers  -f $CWD/template.json && oc replace -f $CWD/template.json || oc ${NS} create -f $CWD/template.json
_oc ${NS} process cccp-service -v SOURCE_REPOSITORY_URL=${REPO},TARGET_NAMESPACE=${NAME},TAG=${TAG},REPO_BUILD_PATH=${REPO_BUILD_PATH} | oc ${NS} create -f -

IP="bs.pco.centos.org"
#$(ip -f inet addr show eth1 2> /dev/null | grep 'inet' | awk '{ print $2}' | sed 's#/.*##')

BUILD=$(_oc ${NS} start-build build)

[ $? -eq 0 ] && echo -e "Build ${BUILD} started.\nYou can watch builds progress at https://${IP}:8443/console/project/${NAME}/browse/builds"
