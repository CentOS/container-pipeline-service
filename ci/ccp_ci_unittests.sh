# copied from the devtools repo
set +e
export CICO_API_KEY=$(cat ~/duffy.key )
read CICO_hostname CICO_ssid <<< $(cico node get -f value -c ip_address -c comment)
echo "duffy node $CICO_hostname"
echo "duff node ssid ${CICO_ssid}"
sshopts="-t -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -l root"
ssh_cmd="ssh $sshopts $CICO_hostname"
$ssh_cmd "yum -y install epel-release && yum -y install rsync git PyYAML python-networkx python2-nose"
rsync -e "ssh $sshopts" -Ha $(pwd)/ $CICO_hostname:payload
$ssh_cmd "cd payload && nosetests -w . -vv tests/"
rtn_code=$?
cico node done $CICO_ssid
exit $rtn_code
