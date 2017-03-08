# copied from the devtools repo
set +e
export CICO_API_KEY=$(cat ~/duffy.key )
read CICO_hostname CICO_ssid <<< $(cico node get -f value -c ip_address -c comment)
sshopts="-t -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -l root"
ssh_cmd="ssh $sshopts $CICO_hostname"
$ssh_cmd "yum -y install rsync git python-virtualenv && virtualenv venv"
$ssh_cmd "source venv/bin/activate && pip install pyyaml networkx && deactivate"
rsync -e "ssh $sshopts" -Ha $(pwd)/ $CICO_hostname:payload
$ssh_cmd git clone https://github.com/CentOS/container-pipeline-service.git 
$ssh_cmd "source venv/bin/activate && python container-pipeline-service/testindex/__init__.py  -i payload/index.d"
rtn_code=$?
cico node done $CICO_ssid
exit $rtn_code
