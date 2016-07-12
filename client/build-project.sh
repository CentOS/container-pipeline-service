#!/usr/bin/bash

ADMIN="--config=/var/lib/origin/openshift.local.config/master/admin.kubeconfig"


function usage() {
    echo "`basename $0` NAME REPO_URL"
    echo "   NAME      Name of the project/namespace"
    echo "   TAG       Name of the resulting image (image will be named NAME/TAG:latest)"
    echo "   REPO_URL  URL of project repository containing Dockerfile"
    echo "   REPO_BRANCH Branch of the repo to be built"
    echo "   REPO_BUILD_PATH  Relative path to the Dockerfile in the repository"
    echo "   TARGET_FILE  Name for the dockerfile to be built"
    echo "   NOTIFY_EMAIL  Email ID to be notified after successful build"
    echo "   DEPENDS_ON  Dependency list for the current image"
    exit 0
}

function _oc() {
    oc $@
}

NAME=$1
TAG=$2
REPO=$3
REPO_BRANCH=$4
REPO_BUILD_PATH=$5
TARGET_FILE=$6
NOTIFY_EMAIL=$7
DEPENDS_ON=$8

[ "${NAME}" == "" ] || [ "${NAME}" == "-h" ] || [ "${NAME}" == "--help" ] && usage
[ "${TAG}" == "" ] && usage
[ "${REPO}" == "" ] && usage
[ "${REPO_BRANCH}" == "" ] && usage
[ "${REPO_BUILD_PATH}" == "" ] && usage
[ "${TARGET_FILE}" == "" ] && usage
[ "${NOTIFY_EMAIL}" == "" ] && usage
[ "${DEPENDS_ON}" == "" ] && usage


CWD=`dirname $0`
NS="--namespace ${NAME}-${TAG}"
echo "==> login to Openshift server"
oc login https://openshift:8443 -u test-admin -p test --certificate-authority=./ca.crt

echo "==>creating new project or using existing project with same name"
oc new-project ${NAME}-${TAG} --display-name=${NAME}-${TAG} || oc project ${NAME}-${TAG}

sed -i.bak s/cccp-service/${NAME}-${TAG}/g $CWD/template.json

echo "==> Uploading template to OpenShift"
for t in $(echo "build bc is"); do
  _oc ${NS} delete $t $(oc get $t -l template=${NAME}-${TAG} --no-headers | awk '{print $1}')
done

_oc ${NS} get --no-headers  -f $CWD/template.json && oc replace -f $CWD/template.json || oc ${NS} create -f $CWD/template.json
_oc ${NS} process ${NAME}-${TAG} -v SOURCE_REPOSITORY_URL=${REPO},REPO_BRANCH=${REPO_BRANCH},TARGET_NAMESPACE=${NAME},TAG=${TAG},REPO_BUILD_PATH=${REPO_BUILD_PATH},TARGET_FILE=${TARGET_FILE},NOTIFY_EMAIL=${NOTIFY_EMAIL} | oc ${NS} create -f -

IP=$(ip -f inet addr show eth1 2> /dev/null | grep 'inet' | awk '{ print $2}' | sed 's#/.*##')

#BUILD=$(_oc ${NS} start-build build)

#[ $? -eq 0 ] && echo -e "Build ${BUILD} started.\nYou can watch builds progress at https://${IP}:8443/console/project/${NAME}/browse/builds"

echo "==> Send build configs to build tube"
python $CWD/send_build_request.py ${NAME} ${TAG} ${DEPENDS_ON}

echo "==> Restoring the default template"
rm -rf $CWD/template.json
mv $CWD/template.json.bak $CWD/template.json

