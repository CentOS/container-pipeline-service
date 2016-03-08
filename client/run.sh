#!/usr/bin/bash

function _() {
    echo "==> $@"
}

_ "Cloning the source repository..."
git clone $SOURCE_REPOSITORY_URL

dirname=${SOURCE_REPOSITORY_URL##*/}
_ "Entering directory ${dirname##*/}"
cd ${dirname##*/}

buildpath=${REPO_BUILD_PATH##/}
if [ "$buildpath" == "" ]; then
    buildpath="."
fi

_ "Building the image in ${buildpath} with tag ${TAG}"
docker build --rm --no-cache -t $TAG ${buildpath}

TO=`python -c 'import json, os; print json.loads(os.environ["BUILD"])["spec"]["output"]["to"]["name"]'`

#TO=${DOCKER_REGISTRY_SERVICE_HOST}:${DOCKER_REGISTRY_SERVICE_PORT}/$TAG

docker tag ${TAG} ${TO}

_ "Pushing the image to registry (${TO})"

if [[ -d /var/run/secrets/openshift.io/push ]] && [[ ! -e /root/.dockercfg ]]; then
  cp /var/run/secrets/openshift.io/push/.dockercfg /root/.dockercfg
fi

if [ -n "${TO}" ] || [ -s "/root/.dockercfg" ]; then
  docker push "${TO}"
fi

_ "Cleaning environment"
docker rmi ${TO} ${TAG}
