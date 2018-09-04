#!/bin/bash
mark_failure()
{
    echo "====================CI-failed====================="
    echo "$1"
    echo "=================================================="
    echo "CI complete releasing the nodes"
    cico node done $cico_node_key
    exit 1
}

set +e
export CICO_API_KEY=$(cat ~/duffy.key)
rtn_code=0

echo "Get nodes from duffy pool"
IFS=' ' read -ra node_details <<< $(cico node get --count 4 -f value -c hostname -c ip_address -c comment)
ansible_node_host=${node_details[0]}.ci.centos.org
ansible_node=${node_details[1]}
nfs_node=${node_details[3]}.ci.centos.org
nfs_node_ip=${node_details[4]}
openshift_1_node=${node_details[6]}.ci.centos.org
openshift_1_node_ip=${node_details[7]}
openshift_2_node=${node_details[9]}.ci.cento.org
openshift_2_node_ip=${node_details[10]}
cico_node_key=${node_details[11]}
cluster_subnet_ip="172.19.2.0"

if [ $cico_node_key == "" ]
then
    mark_failure "Could not get nodes from CICO exiting"
fi

echo "=========================Node Details========================"
echo "Ansible node hostname: $ansible_node_host"
echo "Ansible node: $ansible_node"
echo "NFS node: $nfs_node"
echo "NFS node IP: $nfs_node_ip"
echo "Openshift Node 1: $openshift_1_node"
echo "Openshift Node 1 IP: $openshift_1_node_ip"
echo "Openshift Node 2: $openshift_2_node"
echo "Openshift Node 2 IP: $openshift_2_node_ip"
echo "Node hash: $cico_node_key"
echo "Cluster subnet: $cluster_subnet_ip"
echo "=============================================================\n\n"

git_repo=$1
git_branch=$2
git_actual_commit=$3
echo "========================Git repo details====================="
echo "Base git repo: $git_repo "
echo "Base git branch: $git_branch"
echo "Acutal git commit: $git_actual_commit"
echo "=============================================================\n\n"

export sshopts="-tt -o LogLevel=quiet -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -l root"
export sshoptserr="-tt -o LogLevel=error -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -l root"
echo "Create etc hosts in ansible node"
ssh $sshopts $ansible_node "echo \"$openshift_1_node_ip $openshift_1_node\" >> /etc/hosts"
ssh $sshopts $ansible_node "echo \"$openshift_2_node_ip $openshift_2_node\" >> /etc/hosts"
ssh $sshopts $ansible_node "echo \"$nfs_node_ip $nfs_node\" >> /etc/hosts"

echo "Add ssh keys to all the nodes"
# generate ssh key for ansible node
ssh $sshopts $ansible_node 'rm -rf ~/.ssh/id_rsa* && ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa' >> /dev/null
public_key=$(ssh $sshopts $ansible_node 'cat ~/.ssh/id_rsa.pub')

# Add public key to all the ci nodes
for node in {$nfs_node_ip,$openshift_1_node_ip,$openshift_2_node_ip}
do
    ssh $sshopts $node "echo \"$public_key\" >> ~/.ssh/authorized_keys"
done

echo "Add ssh fringer prints for all node to ansible controller"
for node in {$nfs_node,$openshift_1_node,$openshift_2_node}
do
    ssh $sshopts $ansible_node "ssh-keyscan -t rsa,dsa $node 2>/dev/null >> ~/.ssh/known_hosts"
done

echo "Setup ansible controller node for running openshift 39 deployment"
# setup ansible node
ssh $sshopts $ansible_node 'yum install -y git && yum install -y rsync && yum install -y gcc libffi-devel python-devel openssl-devel && yum install -y epel-release && yum install -y PyYAML python-networkx python-nose python-pep8 python-jinja2 rsync centos-release-openshift-origin39.noarch && yum install -y http://cbs.centos.org/kojifiles/packages/ansible/2.5.5/1.el7/noarch/ansible-2.5.5-1.el7.noarch.rpm && yum install -y openshift-ansible' >> /dev/null

echo "Copy source code to ansible controller node"
rsync -e "ssh -t -o LogLevel=error -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -l root" -Ha ../ $ansible_node:/opt/ccp-openshift

echo "Prepare ansible inventory for service setup"
# generate inventory file for service deployment
ssh $sshoptserr $ansible_node sed -i "s/nfs_serv/$nfs_node/g" /opt/ccp-openshift/provision/files/hosts.ci
ssh $sshoptserr $ansible_node sed -i "s/openshift_1/$openshift_1_node/g" /opt/ccp-openshift/provision/files/hosts.ci
ssh $sshoptserr $ansible_node sed -i "s/openshift_2/$openshift_2_node/g" /opt/ccp-openshift/provision/files/hosts.ci
ssh $sshoptserr $ansible_node sed -i "s/openshift_ip_1/$openshift_1_node_ip/g" /opt/ccp-openshift/provision/files/hosts.ci
ssh $sshoptserr $ansible_node sed -i "s/openshift_ip_2/$openshift_2_node_ip/g" /opt/ccp-openshift/provision/files/hosts.ci
ssh $sshoptserr $ansible_node sed -i "s/cluster_subnet_ip/$cluster_subnet_ip/g" /opt/ccp-openshift/provision/files/hosts.ci
ssh $sshoptserr $ansible_node sed -i "s/oc_username/cccp/g" /opt/ccp-openshift/provision/files/hosts.ci
ssh $sshoptserr $ansible_node sed -i "s/oc_passwd/developer/g" /opt/ccp-openshift/provision/files/hosts.ci


echo "Run ansible playbook for setting service"
#ssh $sshopts $ansible_node 'cd /opt/ccp-openshift/provision && ansible-playbook -i /opt/ccp-openshift/provision/files/hosts.ci main.yaml'
ssh $sshoptserr $ansible_node 'cd /opt/ccp-openshift/provision && ansible-playbook -i /opt/ccp-openshift/provision/files/hosts.ci main.yaml' >> /dev/null
service_setup_done=$?

if [ $service_setup_done -ne 0 ]
then
    mark_failure "Error while deploying the service in CICO"
fi

echo "Cluster is set lets go for tests"

# cico node done ${node_details[2]}

echo "Setting variables for pipeline run"
export PIPELINE_REPO=$git_repo
export PIPELINE_BRANCH=$git_actual_commit
export PIPELINE_BASE_BRANCH=$git_branch

export REGISTRY_URL=$nfs_node:5000
export CONTAINER_INDEX_REPO=https://github.com/CentOS/container-index
export CONTAINER_INDEX_BRANCH=ci
export FROM_ADDRESS=container-build-reports@centos.org
export SMTP_SERVER=smtp://mail.centos.org

echo "Delete build configs if present"
ssh $sshoptserr $openshift_1_node_ip "oc login --username='cccp' --password='developer'"
ssh $sshoptserr $openshift_1_node_ip 'for i in `oc get bc -o name`; do oc delete $i; done'

echo "Command to run"
echo "cd /opt/ccp-openshift && oc process -p PIPELINE_REPO=${PIPELINE_REPO} -p PIPELINE_BRANCH=${PIPELINE_BRANCH} -p REGISTRY_URL=${REGISTRY_URL} -p NAMESPACE=cccp -p CONTAINER_INDEX_REPO=${CONTAINER_INDEX_REPO} -p CONTAINER_INDEX_BRANCH=${CONTAINER_INDEX_BRANCH} -p FROM_ADDRESS=${FROM_ADDRESS} -p SMTP_SERVER=${SMTP_SERVER} -f seed-job/buildtemplate.yaml | oc create -f -"

ssh $sshoptserr $openshift_1_node_ip "cd /opt/ccp-openshift && oc process -p PIPELINE_REPO=${PIPELINE_REPO} -p PIPELINE_BRANCH=${PIPELINE_BRANCH} -p REGISTRY_URL=${REGISTRY_URL} -p NAMESPACE=cccp -p CONTAINER_INDEX_REPO=${CONTAINER_INDEX_REPO} -p CONTAINER_INDEX_BRANCH=${CONTAINER_INDEX_BRANCH} -p FROM_ADDRESS=${FROM_ADDRESS} -p SMTP_SERVER=${SMTP_SERVER} -f seed-job/buildtemplate.yaml | oc create -f -"

echo "Waiting for seed job to complete"
index_read_done=$(ssh $sshopts $openshift_1_node_ip "oc get builds seed-job-1 -o template --template={{.status.phase}}")
echo "Current build status: $index_read_done"

while [[ $index_read_done != 'Complete' && $index_read_done != 'Failed' ]]
do
    sleep 30
    index_read_done=$(ssh $sshopts $openshift_1_node_ip "oc get builds seed-job-1 -o template --template={{.status.phase}}")
done

echo "===========================seed-job-log================="
ssh $sshoptserr $nfs_node_ip "cat /jenkins/jobs/cccp/jobs/cccp-seed-job/builds/1/log"
echo "========================================================"

if [ $index_read_done == 'Failed' ]
then
    mark_failure "ERROR: seed-job failed to process the index"
fi

echo "create CI success job build pipeline"
ssh $sshoptserr $openshift_1_node_ip "cd /opt/ccp-openshift && oc process -f ci/cisuccessjob.yaml | oc create -f -"

echo "Start ci pipeline for success job"
build_id=$(ssh $sshoptserr $openshift_1_node_ip "oc start-build ci-success-job -n cccp |cut -f 2 -d ' '")

echo "Build started with build id: $build_id"

build_id=$(echo $build_id|tr -d '"'|tr -d '\r')

echo "Trimmed build id is: ===$build_id==="

echo "Waiting for the ci to start"
build_status=$(ssh $sshopts $openshift_1_node_ip "oc get builds ${build_id} -o template --template={{.status.phase}}")
echo "Current build status: $build_status"

while [[ $build_status != 'Running' ]]
do
    sleep 30
    build_status=$(ssh $sshopts $openshift_1_node_ip "oc get builds ${build_id} -o template --template={{.status.phase}}")
done

echo "CI for success check started"
echo "Success CI job is: $build_status"
while [[ $build_status != 'Complete' && $build_status != 'Failed' ]]
do
    sleep 30
    build_status=$(ssh $sshopts $openshift_1_node_ip "oc get builds ${build_id} -o template --template={{.status.phase}}")
done

if [ $build_status == 'Failed' ]
then
    echo "=========================Success check build logs==================="
    ssh $sshoptserr $nfs_node_ip "cat /jenkins/jobs/cccp/jobs/cccp-bamachrn-python-release/builds/lastFailedBuild/log"
    echo "===================================================================="
    mark_failure "Success build check failed: FAILURE"
else
    echo "=========================Success check build logs==================="
    ssh $sshoptserr $nfs_node_ip "cat /jenkins/jobs/cccp/jobs/cccp-bamachrn-python-release/builds/lastSuccessfulBuild/log"
    echo "===================================================================="
    echo "Success Build check Passed: SUCCESS"
fi

echo "create CI failure job build pipeline"
ssh $sshoptserr $openshift_1_node_ip "cd /opt/ccp-openshift && oc process -f ci/cifailurejob.yaml | oc create -f -"

echo "Start ci pipeline for success job"
build_id=$(ssh $sshoptserr $openshift_1_node_ip "oc start-build ci-failure-job -n cccp |cut -f 2 -d ' '")

echo "Build started with build id: $build_id"

build_id=$(echo $build_id|tr -d '"'|tr -d '\r')

echo "Trimmed build id is: ===$build_id==="

echo "Waiting for the ci to start"
build_status=$(ssh $sshopts $openshift_1_node_ip "oc get builds ${build_id} -o template --template={{.status.phase}}")
echo "Current build status: $build_status"

while [[ $build_status != 'Running' ]]
do
    sleep 30
    build_status=$(ssh $sshopts $openshift_1_node_ip "oc get builds ${build_id} -o template --template={{.status.phase}}")
done

echo "CI for Fail check started"
echo "Fail check CI job is: $build_status"
while [[ $build_status != 'Complete' && $build_status != 'Failed' ]]
do
    sleep 30
    build_status=$(ssh $sshopts $openshift_1_node_ip "oc get builds ${build_id} -o template --template={{.status.phase}}")
done

echo "========================Fail check build logs==========================="
ssh $sshoptserr $nfs_node_ip "cat /jenkins/jobs/cccp/jobs/cccp-nshaikh-build-fail-test-latest/builds/lastFailedBuild/log"
echo "========================================================================"

if [ $build_status == 'Failed' ]
then
    mark_failure "Failed build check failed: FAILURE"
else
    echo "Failed Build check Passed: SUCCESS"
fi

echo "CI complete releasing the nodes"
cico node done $cico_node_key
