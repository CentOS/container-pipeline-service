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

_ "Cloning the source repository..."
git clone $SOURCE_REPOSITORY_URL||jumpto sendstatusmail


dirname=${SOURCE_REPOSITORY_URL##*/}
_ "Entering directory ${dirname##*/}"
cd ${dirname##*/}

_ "Changing repo branch ${REPO_BRANCH}"
git checkout $REPO_BRANCH||jumpto sendstatusmail

buildpath=${REPO_BUILD_PATH##/}
if [ "$buildpath" == "" ]; then
    buildpath="."
fi

_ "Going to build path "
cd ${buildpath}

_ "Checking cccp.yml exists or rename similar"
if [ ! -f cccp.yml ]; then
    mv *cccp.y*ml cccp.yml
    mv .cccp.y*ml cccp.yml
fi

_ "Copying index reader to docker file"
cp /cccp_reader.py .

_ "Adding index reader to docker file"
echo "ADD cccp_reader.py /set_env/" >> $TARGET_FILE
echo "ADD cccp.yml /set_env/" >> $TARGET_FILE
echo "RUN yum install --disablerepo=* --enablerepo=base -y PyYAML libyaml && python /set_env/cccp_reader.py" >> $TARGET_FILE

_ "Building the image in ${buildpath} with tag ${TAG}"
docker build --rm --no-cache -t $TAG -f $TARGET_FILE . || jumpto sendstatusmail

#_ "Checking local files form container"
#ls -a /set_env/

_ "Setting the environment for running the scripts"
docker run --rm -v /cccp_index_reader.py:/set_env/cccp_index_reader.py $TAG --entrypoint /bin/bash python /set_env/cccp_index_reader.py

_ "Running build steps"
docker run --rm $TAG --entrypoint /bin/bash /usr/bin/build_script

TO=`python -c 'import json, os; print json.loads(os.environ["BUILD"])["spec"]["output"]["to"]["name"]'`

#TO=${DOCKER_REGISTRY_SERVICE_HOST}:${DOCKER_REGISTRY_SERVICE_PORT}/$TAG

docker tag ${TAG} ${TO}

_ "Pushing the image to registry (${TO})"

if [[ -d /var/run/secrets/openshift.io/push ]] && [[ ! -e /root/.dockercfg ]]; then
  _ "Copying the dockercfg to home dir"
  cp /var/run/secrets/openshift.io/push/.dockercfg /root/.dockercfg
fi

if [ -n "${TO}" ] || [ -s "/root/.dockercfg" ]; then
  docker push "${TO}" || jumpto sendstatusmail
fi

_ "Cleaning environment"
docker rmi ${TAG}
jumpto end

sendstatusmail:
_ "Sending mail of failed status to ${NOTIFY_EMAIL}"
docker run --rm mail-server /usr/bin/mail-config.sh "Current status is failed" ${NOTIFY_EMAIL}

end:
  exit 0
