#!/usr/bin/bash

CWD=`dirname $0`

function usage() {
    echo "`basename $0` [try]"
    echo "try    Deploys template and build workflow and start's a build"
}

[ "$1" == "help" ] || [ "$1" == "-h" ] || [ "$1" == "--help" ] && usage

echo "==> Building cccp-build image"
docker build -t cccp-build -f $CWD/Dockerfile.build $CWD || exit 1
echo "==> Building cccp-test image"
docker build -t cccp-test -f $CWD/Dockerfile.test $CWD || exit 1
echo "==> Building cccp-delivery image"
docker build -t cccp-delivery -f $CWD/Dockerfile.delivery $CWD || exit 1



if [ "$1" == "try" ]; then
    echo "==> Uploading template to OpenShift"
    for t in $(echo "build bc is"); do
        oc delete $t $(oc get $t -l template=cccp-demo --no-headers | awk '{print $1}')
    done
    oc get --no-headers  -f $CWD/template.json && oc replace -f $CWD/template.json || oc create -f $CWD/template.json
    oc process cccp-demo -v SOURCE_REPOSITORY_URL=https://github.com/vpavlin/cccp-demo-proj | oc create -f -
    oc start-build build
else
    echo "You can also run this script with parameter 'try' to delpoy a template and example build workflow and start a build"
fi
