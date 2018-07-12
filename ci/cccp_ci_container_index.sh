# copied from the devtools repo
set +e
export CICO_API_KEY=$(cat ~/duffy.key )
read CICO_hostname CICO_ssid <<< $(cico node get -f value -c ip_address -c comment)
sshopts="-t -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -l root"
ssh_cmd="ssh $sshopts $CICO_hostname"
$ssh_cmd "yum -y install epel-release && yum -y install rsync git PyYAML python-networkx"
rsync -e "ssh $sshopts" -Ha $(pwd)/ $CICO_hostname:payload
#$ssh_cmd git clone https://github.com/CentOS/container-pipeline-service.git 
$ssh_cmd git clone https://github.com/mohammedzee1000/container-pipeline-service.git
$ssh_cmd git fetch --all
$ssh_cmd git checkout origin/index_ci_refac_6
$ssh_cmd /usr/bin/python container-pipeline-service/ci/container_index/run.py  -vi ./payload
rtn_code=$?
cico node done $CICO_ssid
exit $rtn_code
