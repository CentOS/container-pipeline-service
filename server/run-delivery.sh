#!/usr/bin/bash

function _() {
    echo "==> $@"
}
TOKEN=`cat /var/run/secrets/kubernetes.io/serviceaccount/token`

NFS_SHARE="/srv/pipeline-logs"
LOGS_DIR="${NFS_SHARE}/${TEST_TAG}"

if [ "${TARGET_REGISTRY}" == "" ];then
    TARGET_REGISTRY=${INTERNAL_REGISTRY}
fi

FULL_FROM=${INTERNAL_REGISTRY}/${APPID}/${FROM}
FULL_TO=${TARGET_REGISTRY}/${APPID}/${TO}

_ "Pulling RC image (${FROM})"
docker pull ${FULL_FROM}

sleep 20

_ "Tagging for the public registry"
docker tag ${FULL_FROM} ${FULL_TO}

_ "Pushing final image (${FULL_TO})"
docker push ${FULL_TO}

OUTPUT_IMAGE=registry.centos.org/${APPID}/${TO}

NS="${APPID}-${JOBID}-${DESIRED_TAG}"

_ "Send success mail for user notify tube"
python /tube_request/send_notify_request.py ${BEANSTALK_SERVER} ${OUTPUT_IMAGE} ${NOTIFY_EMAIL} ${TEST_TAG} ${NS} ${JOBID} ${LOGS_DIR}

_ "Cleaning environment"
docker rmi ${FULL_FROM} ${FULL_TO}
