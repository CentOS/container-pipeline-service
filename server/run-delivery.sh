#!/usr/bin/bash

function _() {
    echo "==> $@"
}
TOKEN=`cat /var/run/secrets/kubernetes.io/serviceaccount/token`

if [ "${TARGET_REGISTRY}" == "" ];then
    TARGET_REGISTRY=${OUTPUT_REGISTRY}
fi

_ "Log in to the internal registry"
docker login -u serviceaccount -p ${TOKEN} -e serviceaccount@example.org ${OUTPUT_REGISTRY}

FULL_FROM=${OUTPUT_REGISTRY}/`python -c 'import json, os; print json.loads(os.environ["BUILD"])["metadata"]["namespace"]'`/${FROM}
FULL_TO=${TARGET_REGISTRY}/${TARGET_NAMESPACE}/${TO}

_ "Pulling RC image (${FROM})"
docker pull ${FULL_FROM}

_ "Running delivery steps"
docker run --rm ${FULL_FROM} /bin/bash /usr/bin/delivery_script

sleep 20

_ "Tagging for the public registry"
docker tag ${FULL_FROM} ${FULL_TO}

_ "Pushing final image (${FULL_TO})"
docker push ${FULL_TO}

OUTPUT_IMAGE=i10.lon0.centos.in/${TARGET_NAMESPACE}/${TO}
_ "Send mail to notify build is completed"
echo "Build is successful please pull the image (${OUTPUT_IMAGE})" | mail -s "cccp-build is complete" ${NOTIFY_EMAIL}

_ "Cleaning environment"
docker rmi ${FULL_FROM} ${FULL_TO}
