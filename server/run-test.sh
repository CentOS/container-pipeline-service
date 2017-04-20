#!/usr/bin/bash

NFS_SHARE="/srv/pipeline-logs"
LOGS_DIR="${NFS_SHARE}/${TEST_TAG}"

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
FULL_TO=${TARGET_REGISTRY}/${APPID}/${TO}


_ "Pulling tested image (${FULL_FROM})"
docker pull ${FULL_FROM} || jumpto sendstatusmail

#_ "Checking if test script is getting success"
#if [ `docker run --rm ${FULL_FROM} /bin/bash ls /usr/bin/test_script;echo $?` -eq 0 ]; then
#docker run --rm ${FULL_FROM} --entrypoint /bin/bash /usr/bin/test_script
#|| jumpto sendstatusmail
#fi

_ "Re-tagging tested image (${FULL_FROM} -> ${FULL_TO})"
docker tag ${FULL_FROM} ${FULL_TO} || jumpto sendstatusmail
NS="${APPID}-${JOBID}-${DESIRED_TAG}"
OUTPUT_IMAGE=${TARGET_REGISTRY}/${APPID}/${TO}
IMAGE_NAME=${APPID}/${JOBID}:${DESIRED_TAG}

_ "Pushing the image to registry (${OUTPUT_IMAGE})"
#if [ -n "${FULL_TO}" ] || [ -s "/root/.dockercfg" ]; then
#  docker push "${FULL_TO}" || jumpto sendstatusmail
#fi
docker push ${FULL_TO}||jumpto sendstatusmail

python /tube_request/send_scan_request.py ${BEANSTALK_SERVER} ${NS} ${OUTPUT_IMAGE} ${TEST_TAG} ${NOTIFY_EMAIL} ${LOGS_DIR} ${JOBID}

_ "Cleaning environment"
docker rmi ${FULL_FROM}
jumpto end

sendstatusmail:
  exit 1

end:
  exit 0
