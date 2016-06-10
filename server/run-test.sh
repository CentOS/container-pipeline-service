#!/usr/bin/bash

function _() {
    echo "==> $@"
}

function jumpto
{
    label=$1
    cmd=$(sed -n "/$label:/{:a;n;p;ba};" $0 | grep -v ':$')
    eval "$cmd"
    exit
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
docker pull ${FULL_FROM} || jumpto sendstatusmail

_ "Checking if test script is getting success"
if [ `docker run --rm ${FULL_FROM} ls /usr/bin/test_script` -eq 0 ]; then
   docker run --rm ${FULL_FROM} /bin/bash /usr/bin/test_script || jumpto sendstatusmail
fi

_ "Re-tagging tested image (${FULL_FROM} -> ${TO})"
docker tag ${FULL_FROM} ${FULL_TO} || jumpto sendstatusmail

_ "Pushing the image to registry (${FULL_TO})"


if [ -n "${FULL_TO}" ] || [ -s "/root/.dockercfg" ]; then
  docker push "${FULL_TO}" || jumpto sendstatusmail
fi

_ "Cleaning environment"
docker rmi ${FULL_FROM}

sendstatusmail:
_ "Sending mail of failed status to ${NOTIFY_EMAIL}"
docker run --rm mail-server /usr/bin/mail-config.sh "Current status is failed" ${NOTIFY_EMAIL}
