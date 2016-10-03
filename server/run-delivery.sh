#!/usr/bin/bash

function _() {
    echo "==> $@"
}
TOKEN=`cat /var/run/secrets/kubernetes.io/serviceaccount/token`

if [ "${TARGET_REGISTRY}" == "" ];then
    TARGET_REGISTRY=${OUTPUT_REGISTRY}
fi

FULL_FROM=${TARGET_REGISTRY}/${TARGET_NAMESPACE}/${FROM}
FULL_TO=${TARGET_REGISTRY}/${TARGET_NAMESPACE}/${TO}

_ "Pulling RC image (${FROM})"
docker pull ${FULL_FROM}

sleep 20

_ "Tagging for the public registry"
docker tag ${FULL_FROM} ${FULL_TO}

_ "Pushing final image (${FULL_TO})"
docker push ${FULL_TO}

OUTPUT_IMAGE=registry.centos.org/${TARGET_NAMESPACE}/${TO}

#_ "Send mail to (${NOTIFY_EMAIL}) notify build is completed (${OUTPUT_IMAGE})"
#echo "Build is successful please pull the image (${OUTPUT_IMAGE})" | mail -r container-build-report@centos.org -s "cccp-build is complete" ${NOTIFY_EMAIL}

#sleep 20

python /tube_request/send_notify_request.py ${BEANSTALK_SERVER} ${OUTPUT_IMAGE} ${NOTIFY_EMAIL}

_ "Cleaning environment"
docker rmi ${FULL_FROM} ${FULL_TO}
