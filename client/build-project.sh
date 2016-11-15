#!/usr/bin/bash

ADMIN="--config=/var/lib/origin/openshift.local.config/master/admin.kubeconfig"


function usage() {
    echo "`basename $0` NAME REPO_URL"
    echo "   APPID      Name of the project/namespace"
    echo "   JOBID       Name of the resulting image (image will be named APPID/JOBID:DESIRED_TAG)"
    echo "   REPO_URL  URL of project repository containing Dockerfile"
    echo "   REPO_BRANCH Branch of the repo to be built"
    echo "   REPO_BUILD_PATH  Relative path to the Dockerfile in the repository"
    echo "   TARGET_FILE  Name for the dockerfile to be built"
    echo "   NOTIFY_EMAIL  Email ID to be notified after successful build"
    echo "   DEPENDS_ON  Dependency list for the current image"
    echo "   DESIRED_TAG  Tag for the final output image like latest"
    exit 0
}

function _oc() {
    oc --config=./node.kubeconfig $@
}

APPID=$1
JOBID=$2
REPO=$3
REPO_BRANCH=$4
REPO_BUILD_PATH=$5
TARGET_FILE=$6
NOTIFY_EMAIL=$7
DESIRED_TAG=$8
DEPENDS_ON=$9
TEST_TAG=`date +"%Y%m%d%H%M%S"`

[ "${APPID}" == "" ] || [ "${APPID}" == "-h" ] || [ "${APPID}" == "--help" ] && usage
[ "${JOBID}" == "" ] && usage
[ "${REPO}" == "" ] && usage
[ "${REPO_BRANCH}" == "" ] && usage
[ "${REPO_BUILD_PATH}" == "" ] && usage
[ "${TARGET_FILE}" == "" ] && usage
[ "${NOTIFY_EMAIL}" == "" ] && usage
[ "${DEPENDS_ON}" == "" ] && usage
[ "${DESIRED_TAG}" == "" ] && usage


CWD=`dirname $0`
PN="${APPID}-${JOBID}-${DESIRED-TAG}"
NS="--namespace ${PN}"

echo "==> login to Openshift server"
OPENSHIFT_SERVER_IP=`ping OPENSHIFT_SERVER_HOST -c 1 | awk '{print $3}'|head -n 1|sed 's/(//'|sed 's/)//'`
_oc login https://${OPENSHIFT_SERVER_IP}:8443 -u test-admin -p test --certificate-authority=./ca.crt

echo "==>creating new project or using existing project with same name"
_oc new-project ${PN} --display-name=${PN} || _oc project ${PN}

sed -i.bak s/cccp-service/${PN}/g $CWD/template.json

echo "==> Uploading template to OpenShift"
for t in $(echo "build bc is"); do
  _oc ${NS} delete $t $(_oc get $t -l template=${PN} --no-headers | awk '{print $1}')
done

_oc ${NS} get --no-headers  -f $CWD/template.json && _oc replace -f $CWD/template.json || _oc ${NS} create -f $CWD/template.json
_oc ${NS} process ${PN} -v SOURCE_REPOSITORY_URL=${REPO},REPO_BRANCH=${REPO_BRANCH},TARGET_NAMESPACE=${APPID},TAG=${JOBID},REPO_BUILD_PATH=${REPO_BUILD_PATH},TARGET_FILE=${TARGET_FILE},NOTIFY_EMAIL=${NOTIFY_EMAIL},TEST_TAG=${TEST_TAG},DESIRED_TAG=${DESIRED_TAG} | _oc ${NS} create -f -

IP=$(ip -f inet addr show eth1 2> /dev/null | grep 'inet' | awk '{ print $2}' | sed 's#/.*##')

#BUILD=$(_oc ${NS} start-build build)

#[ $? -eq 0 ] && echo -e "Build ${BUILD} started.\nYou can watch builds progress at https://${IP}:8443/console/project/${NAME}/browse/builds"

echo "==> Send build configs to build tube"
python $CWD/send_build_request.py ${APPID} ${JOBID} ${DESIRED_TAG} ${REPO_BRANCH} ${REPO_BUILD_PATH} ${TARGET_FILE} ${NOTIFY_EMAIL} ${DEPENDS_ON}

echo "==> Restoring the default template"
rm -rf $CWD/template.json
mv $CWD/template.json.bak $CWD/template.json
