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

if [[ -d /var/run/secrets/openshift.io/push ]] && [[ ! -e /root/.dockercfg ]]; then
  cp /var/run/secrets/openshift.io/push/.dockercfg /root/.dockercfg
fi

FULL_FROM=${OUTPUT_REGISTRY}/`python -c 'import json, os; print json.loads(os.environ["BUILD"])["metadata"]["namespace"]'`/${FROM}
FULL_TO=`python -c 'import json, os; print json.loads(os.environ["BUILD"])["spec"]["output"]["to"]["name"]'`

_ "Pulling tested image (${FULL_FROM})"
docker pull ${FULL_FROM} || jumpto sendstatusmail

_ "Checking if test script is getting success"
if [ `docker run --rm ${FULL_FROM} /bin/bash ls /usr/bin/test_script;echo $?` -eq 0 ]; then
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
jumpto end

sendstatusmail:
_ "Sending mail of failed status to ${NOTIFY_EMAIL}"
docker run --rm mail-server /usr/bin/mail-config.sh "Current status is failed" ${NOTIFY_EMAIL}

end:
  exit 0
