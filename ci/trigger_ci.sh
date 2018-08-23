set +e
export CICO_API_KEY=$(cat ~/duffy.key)
IFS=' ' read -ra node_details <<< $(cico node get --count 4 -f value -c ip_address -c comment)
ansible_node=node_details[0]
nfs_node=node_details[2]
openshif_1_node=node_details[4]
openshif_2_node=node_details[5]
export sshopts="-t -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -l root"

# generate ssh key for ansible node
ssh $sshopts $ansible_node 'rm -rf ~/.ssh/id_rsa* && ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa'
public_key=$(ssh $sshopts $ansible_node 'cat ~/.ssh/id_rsa.pub')

# Add public key to all the ci nodes
for node in {$nfs_node,$openshif_1_node,$openshif_2_node}
do
    ssh $sshopts $node 'echo "$public_key" >> ~/.ssh/authorized_keys'
done

# setup ansible node
ssh $sshopts $ansible_node 'yum install -y git && yum install -y rsync && yum install -y gcc libffi-devel python-devel openssl-devel && yum install -y epel-release && yum install -y PyYAML python-networkx python-nose python-pep8 python-jinja2 && yum install -y http://cbs.centos.org/kojifiles/packages/ansible/2.5.5/1.el7/noarch/ansible-2.5.5-1.el7.noarch.rpm'



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
