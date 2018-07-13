for i in `oc get bc -o name`; do oc delete $i; done
cd
rm -rf ccp-openshift/
git clone https://github.com/bamachrn/ccp-openshift/
cd ccp-openshift
git checkout ci-functional
export CI_PIPELINE_REPO=https://github.com/bamachrn/ccp-openshift/
export CI_PIPELINE_BRANCH=ci-functional
export PIPELINE_REPO=https://github.com/bamachrn/ccp-openshift/
export PIPELINE_BRANCH=ci-functional
export REGISTRY_URL=172.29.33.54:5000
export CONTAINER_INDEX_REPO=https://github.com/bamachrn/ccp-openshift-index
export CONTAINER_INDEX_BRANCH=ci
# export FROM_ADDRESS=container-build-reports@centos.org
# export SMTP_SERVER=smtp://mail.centos.org
oc process -p PIPELINE_REPO=${PIPELINE_REPO} -p PIPELINE_BRANCH=${PIPELINE_BRANCH} -p REGISTRY_URL=${REGISTRY_URL} -p NAMESPACE=`oc project -q` -p CONTAINER_INDEX_REPO=${CONTAINER_INDEX_REPO} -p CONTAINER_INDEX_BRANCH=${CONTAINER_INDEX_BRANCH} -f seed-job/buildtemplate.yaml | oc create -f -

#create CI job build pipeline
oc process -p CI_PIPELINE_REPO=${CI_PIPELINE_REPO} -p CI_PIPELINE_BRANCH=${CI_PIPELINE_BRANCH} -f ci/cijobtemplate.yaml | oc create -f -
