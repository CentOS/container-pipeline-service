#!/bin/bash

set +e

mark_failure()
{
    echo "==================Unittests-CI-failed================="
    echo "$1"
    echo "======================================================"
    if [ $CI_DEBUG -eq 0 ]
    then
      echo "Unittests CI is complete, releasing the node(s)."
      cico node done $CICO_ssid
    else
      echo "========================================================================"
      echo "DEBUG mode is set for CI, keeping the node(s) for 2 hours for debugging."
      echo "========================================================================"
      sleep $DEBUG_PERIOD
    fi
    exit 1
}

export CICO_API_KEY=$(cat ~/duffy.key)
rtn_code=0
# debug period = 2 hours = 7200 seconds
DEBUG_PERIOD=7200
# grab the CI_DEBUG flag's value, 0 or 1
CI_DEBUG=$1

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
echo "duff node ssid $CICO_ssid"
echo "DEBUG mode is set to: $CI_DEBUG"
echo "=========================================================="


sshopts="-t -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -l root"
ssh_cmd="ssh $sshopts $CICO_hostname"

echo "====Installing necessary packages for running tests on the duffy node===="
# install the needed packages on the duffy node which will the tests
$ssh_cmd "yum -y install epel-release && yum -y install rsync git PyYAML python-networkx python2-nose python-requests" >> /tmp/unittests_setup_log.txt
package_installed_success=$?

if [ $package_installed_success -ne 0 ]
then
  echo "==================Package Installation Logs============"
  cat /tmp/unittests_setup_log.txt
  echo "======================================================="
  mark_failure "Failed to install required packages on duffy node, exiting!"
fi
echo "====Duffy node is setup with necessary dependencies===="

echo "======Copying source code to the duffy node======"
# sync the codebase from PR to duffy node
rsync -e "ssh $sshopts" -Ha $(pwd)/ $CICO_hostname:payload
rsync_success=$?

if [ $rsync_success -ne 0 ]
then
  mark_failure "Failed to rsync the PR source code on duffy node, exiting!"
fi
echo "======Source code coppied to the duffy node======"

echo "==================Running the unit tests==============="
# run the unittests on duffy node
$ssh_cmd "cd payload && nosetests -w . -vv tests/"
rtn_code=$?
echo "======================================================="


if [ $CI_DEBUG -eq 0 ]
then
    echo "Unittests CI is complete, releasing the nodes."
    cico node done $CICO_ssid
else
    echo "========================================================================"
    echo "DEBUG mode is set for CI, keeping the node(s) for 2 hours for debugging."
    echo "========================================================================"
    sleep $DEBUG_PERIOD
fi

exit $rtn_code
