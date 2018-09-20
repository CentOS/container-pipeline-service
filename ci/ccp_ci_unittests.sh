#!/bin/bash

set +e

mark_failure()
{
    echo "==================Unittests-CI-failed================="
    echo "$1"
    echo "======================================================"
    cico node done $CICO_ssid
    exit 1
}

export CICO_API_KEY=$(cat ~/duffy.key)
rtn_code=0

echo "Requesting the node(s) from duffy pool.."

read CICO_hostname CICO_ssid <<< $(cico node get -f value -c ip_address -c comment)
rtn_code=$?

# check if we received the nodes from duffy
if [ -z "$CICO_hostname" ] || [ -z "$CICO_ssid" ] || [ $rtn_code -ne 0 ]
then
  mark_failure "Could not get a node from duffy, exiting!"
fi

echo "=====================Node Details========================="
echo "duffy node $CICO_hostname"
echo "duff node ssid ${CICO_ssid}"
echo "=========================================================="

sshopts="-t -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -l root"
ssh_cmd="ssh $sshopts $CICO_hostname"

# install the needed packages on the duffy node which will the tests
$ssh_cmd "yum -y install epel-release && yum -y install rsync git PyYAML python-networkx python2-nose"
package_installed_success=$?

if [ $package_installed_success -ne 0]
then

  mark_failure "Failed to install required packages on duffy node, exiting!"
fi


# sync the codebase from PR to duffy node
rsync -e "ssh $sshopts" -Ha $(pwd)/ $CICO_hostname:payload
rsync_success=$?

if [ $rsync_success -ne 0]
then
  mark_failure "Failed to rsync the PR source code on duffy node, exiting!"
fi

# run the unittests on duffy node
$ssh_cmd "cd payload && nosetests -w . -vv tests/"
rtn_code=$?

cico node done $CICO_ssid

exit $rtn_code
