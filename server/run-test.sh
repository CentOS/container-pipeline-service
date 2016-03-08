#!/usr/bin/bash

function _() {
    echo "==> $@"
}

_ "[FAKE] Talking to Jenkins: Please, test the repository ${SOURCE_REPOSITORY_URL}, tests are located in ${REPO_TEST_PATH}"
_ "[FAKE] Jenkins running..."
_ "[FAKE] Jenkins returned: PASS"

if [[ -d /var/run/secrets/openshift.io/push ]] && [[ ! -e /root/.dockercfg ]]; then
  cp /var/run/secrets/openshift.io/push/.dockercfg /root/.dockercfg
fi

FULL_FROM=${OUTPUT_REGISTRY}/`python -c 'import json, os; print json.loads(os.environ["BUILD"])["metadata"]["namespace"]'`/${FROM}
FULL_TO=`python -c 'import json, os; print json.loads(os.environ["BUILD"])["spec"]["output"]["to"]["name"]'`

_ "Pulling tested image (${FULL_FROM})"
docker pull ${FULL_FROM}
_ "Re-tagging tested image (${FULL_FROM} -> ${TO})"
docker tag ${FULL_FROM} ${FULL_TO}

_ "Pushing the image to registry (${FULL_TO})"


if [ -n "${FULL_TO}" ] || [ -s "/root/.dockercfg" ]; then
  docker push "${FULL_TO}"
fi

_ "Cleaning environment"
docker rmi ${FULL_FROM} ${FULL_TO}
