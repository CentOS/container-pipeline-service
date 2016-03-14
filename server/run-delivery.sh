#!/usr/bin/bash

function _() {
    echo "==> $@"
}
TOKEN=`cat /var/run/secrets/kubernetes.io/serviceaccount/token`

if [ "${TARGET_REGISTRY}" == "" ];then
    TARGET_REGISTRY=${OUTPUT_REGISTRY}
fi

docker login -u serviceaccount -p ${TOKEN} -e serviceaccount@example.org ${OUTPUT_REGISTRY}

FULL_FROM=${OUTPUT_REGISTRY}/`python -c 'import json, os; print json.loads(os.environ["BUILD"])["metadata"]["namespace"]'`/${FROM}
FULL_TO=${TARGET_REGISTRY}/${TARGET_NAMESPACE}/${TO}

_ "Pulling RC image (${FROM})"
docker pull ${FULL_FROM}

_ "Running delivery steps"
docker run --rm ${FULL_FORM} /bin/bash /usr/bin/delivery_script

_ "Tagging for the public registry"
docker tag ${FULL_FROM} ${FULL_TO}

wget dev-32-43.lon1.centos.org/certs/dev-32-43.lon1.centos.org.crt

mkdir -p /etc/docker/certs.d/dev-32-43.lon1.centos.org/

cp ./dev-32-43.lon1.centos.org.crt /etc/docker/certs.d/dev-32-43.lon1.centos.org/ca.crt

#if [[ -d /var/run/secrets/openshift.io/push ]] && [[ ! -e /root/.dockercfg ]]; then
#  cp /var/run/secrets/openshift.io/push/ca.crt /etc/docker/certs.d/dev-32-43.lon1.centos.org/ca.crt
#fi
_ "Pushing final image (${FULL_TO})"
docker push ${FULL_TO}

_ "Cleaning environment"
docker rmi ${FULL_FROM} ${FULL_TO}
