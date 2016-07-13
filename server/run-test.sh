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
#FULL_TO=`python -c 'import json, os; print json.loads(os.environ["BUILD"])["spec"]["output"]["to"]["name"]'`
FULL_TO=${TARGET_REGISTRY}/${TARGET_NAMESPACE}/${TO}


_ "Pulling tested image (${FULL_FROM})"
docker pull ${FULL_FROM} || jumpto sendstatusmail

_ "Checking if test script is getting success"
#if [ `docker run --rm ${FULL_FROM} /bin/bash ls /usr/bin/test_script;echo $?` -eq 0 ]; then
docker run --rm ${FULL_FROM} --entrypoint /bin/bash /usr/bin/test_script 
#|| jumpto sendstatusmail
#fi

_ "Re-tagging tested image (${FULL_FROM} -> ${FULL_TO})"
docker tag ${FULL_FROM} ${FULL_TO} || jumpto sendstatusmail

OUTPUT_IMAGE=registry.centos.org/${TARGET_NAMESPACE}/${TO}

_ "Pushing the image to registry (${OUTPUT_IMAGE})"
#if [ -n "${FULL_TO}" ] || [ -s "/root/.dockercfg" ]; then
#  docker push "${FULL_TO}" || jumpto sendstatusmail
#fi
docker push ${FULL_TO}||jumpto sendstatusmail
python /tube_request/send_test_request.py ${BEANSTALK_SERVER} ${NS} ${OUTPUT_IMAGE} "rc"


_ "Cleaning environment"
docker rmi ${FULL_FROM}
jumpto end

sendstatusmail:
_ "Sending mail of failed status to ${NOTIFY_EMAIL}"
docker run --rm mail-server /usr/bin/mail-config.sh "Current status is failed" ${NOTIFY_EMAIL}

end:
  exit 0
