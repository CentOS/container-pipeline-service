#!/bin/bash

#############################
# VARIABLES                 #
#############################

# Setup the SSH passwords
PASS=root

# What hosts and ips we're going to be using
hosts=( "cccp-jenkins-master" "cccp-jenkins-slave" "cccp-openshift" "cccp-scanner")
ips=( "192.168.10.10" "192.168.10.20" "192.168.10.30" "192.168.10.40")
subnet="192.168.10.0/24"
gateway="192.168.10.1"



up() {
  #############################
  # PRE                       #
  #############################

  # Check to see if sshpass is installed
  if ! hash sshpass 2>/dev/null; then
    echo "ERROR: No 'sshpass' binary detected. Please run 'yum install sshpass' or 'apt-get install sshpass'"
    exit 0
  fi

  # Create the private network
  echo "================================="
  echo "Creating private Docker network  "
  echo "================================="
  docker network create --subnet $subnet --gateway $gateway cccp


  # Create the log files
  echo ""
  echo "================================="
  echo "Generate pipeline-logs folder    "
  echo "================================="
  mkdir pipeline-logs || true
  chmod -R 777 pipeline-logs
  sudo chown nobody:nogroup -R pipeline-logs

  #############################
  # STEPS                     #
  #############################


  for ((i=0;i<${#hosts[@]};++i)); do

      echo ""
      echo "================================="
      echo "Starting ${hosts[i]} at ${ips[i]}"
      echo "================================="


      # Start the container
      # See: https://bugzilla.redhat.com/show_bug.cgi?id=1033604#c17 and https://rhatdan.wordpress.com/2014/04/30/running-systemd-within-a-docker-container/
      # for more information regarding the permissions.
      docker run \
        --name "${hosts[i]}" \
        --hostname "${hosts[i]}" \
        -d -ti \
        --network cccp \
        --ip "${ips[i]}" \
        -v /tmp/$(mktemp -d):/run \
        -v /sys/fs/cgroup:/sys/fs/cgroup:rw \
        -v /sys:/sys:rw \
        -v ${PWD}/pipeline-logs:/srv/pipeline-logs \
        -e "container=docker" \
        --cap-add SYS_ADMIN \
        --security-opt seccomp:unconfined \
        --privileged \
        cdrage/dind-ssh-centos7

      # Change the root password and copy over our public SSH key 
      echo -e "$PASS\n$PASS" | sudo docker exec -i ${hosts[i]} passwd > /tmp/cccp.log 2>&1
      sshpass -p "root" ssh-copy-id -o StrictHostKeyChecking=no root@${ips[i]} > /tmp/cccp.log 2>&1
        
      # CentOS7 container has some weird issues regarding mounting volumes on shared (especially OpenShift)
      docker exec -it ${hosts[i]} mount --make-shared / 

      # TODO (implement into the actual Docker container..)
      # MAGIC, because for some reason, there's no loopback on the centos7 images in order to do docker-in-docker...
      # see: https://github.com/jpetazzo/dind/issues/19
      docker cp loopback.sh ${hosts[i]}:/tmp/loopback.sh
      docker exec -it ${hosts[i]} bash /tmp/loopback.sh

      # Remove /run/nologin so non-root users can login correctly
      docker exec -it ${hosts[i]} rm -f /run/nologin
    done
}

down() {

  for ((i=0;i<${#hosts[@]};++i)); do
    # Remove the container
    echo ""
    echo "================================="
    echo "Removing container ${hosts[i]}   "
    echo "================================="
    docker rm -f ${hosts[i]}

    # Remove the corresponding SSH key
    echo ""
    echo "=================================================="
    echo "Removing SSH key ${hosts[i]} / ${ips[i]} "
    echo "=================================================="
    ssh-keygen -R ${ips[i]}
  done

  echo ""
  echo "======================="
  echo "Removing Docker network"
  echo "======================="
  docker network remove cccp

  echo ""
  echo "==========================="
  echo "Removing pipeline-logs file"
  echo "==========================="
  sudo rm -rf pipeline-logs
}

deploy() {
  echo "==================================================================="
  echo "This is going to take a while (grab a coffee)"
  echo "This requires a fast machine (Core i7 or equivilant, 8GB+ RAM)"
  echo "We will be provisioning and deploying to each container via ansible"
  echo ""
  echo "|--------------------------------|"
  echo "| IP            | HOST           |"
  echo "|--------------------------------|"
  echo "| 192.168.10.10 | jenkins master |"
  echo "| 192.168.10.20 | jenkins slave  |"
  echo "| 192.168.10.30 | openshift      |"
  echo "| 192.168.10.40 | scanner worker |"
  echo "|--------------------------------|"
  echo ""
  echo "==================================================================="
  echo ""

  # Check to see if ansible-playbook is installed
  if ! hash ansible-playbook 2>/dev/null; then
    echo "ERROR: No 'ansible-playbook' binary detected. Please run 'pip install ansible'"
    exit 0
  fi

  # Create the private network
  echo "========================================================="
  echo "Using pre-made SSH keys for Jenkins at /tmp/cccp-jenkins*"
  echo "========================================================="
  echo ""

  cat >/tmp/cccp-jenkins.key <<EOL
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAp7PDAT1mNkDLGL1EbiKa6pokP66SRgUtiYViQNFpQzFGjBkf
qZkPN0nu515Tsoqi6tpZ+1Ab6Bpl47k44OvRVG+ta3pX5VnfaZE9096ltFFjFrMX
AcHMifKB4rr126mbogNXttqbCqYag5xahgoFx/D7+Hd+GlW+wR6YvuS3y206WbE5
LFnbb/5EA+nIVz3L/HzFYn/2r8DGCmDZqXx2IFJoD1MdToKKf370r9unD2J+NALE
UzseMk7z2yuGdAgyflb2y6yY2JHk1eg6jKMbJA0f5Vml5QOuP5S53BCerM2g81mO
IjeiSsvDw36+04azMEsbl1nHfJjRDHYo50db1wIDAQABAoIBAEjEaogeMTy3TqkU
bx3u7BOCANqVEClL09+JPgHsG+Wo+viNajy4Cm8uKHjCaETffSO0zTiMIR/MXIu8
ch6+lF0z/CbXtk3xekyfVhmZ0YL1ka5m1UPQ6MSusodEIqxG4x4gny3bm0y6mGSl
Mm5Y6PtB6MN+bfxVWmkHsrWaHtoofdn2yIonCPBB+OlqT2Hxx4SucR130Wru6vBY
72rJ+VEpyarMbAExvcKUNvRAYCL31eN2lcPXk3bsQ/GdX73WjL3JCKlSmAp2woYc
QcRqNpQ68EnV37dMx+5vt3eWctLoqGi/EE9u8kJyGs0fIKdVQVVzaK4JaXVErwic
seMRGRECgYEA3ihQQ2qAiLwNl+qlVpGLFOurnKOrLTsX6qlUK5tt4LUzc/BdRqPT
Q3drCnJIvM35JhzZhmOsKipYLFus4K1MKSiK9q+0pjdV6bUZjd5hafOZbNMFVFnN
lOyCQPS5BDNrwF4QTC9QFNAEYToNAYbh6xg1HtoydM91sAXvjiH289kCgYEAwT/N
xqO0MAFTPxzZKkhCAF4jfM9sUxqdcW/eWM4ZyBm4fYTEY+9m5iCXaFmvblgPyjqJ
PbKnhuQcKtJ1I0tT3W/Hmm71fvClWDtP7nRxk2MxjfT4ojHAHKmUNxET8CDbmrG4
aMDnMgDNei8dg/NClkAs+mTuACCpxkdxuT7x7y8CgYBV2oCCPTNlJD+gmQbCeMam
FBmjFEE/3pl0j3G+1HdXIs+6m4aAmSk45nqQc/AWPwdtKjMKU5SiSvD+W4No5LAN
K+TgRrDql3H1Oo6gm/NLjd+aBccGfRoM1oXT8n9Z10Fp+zATMSmikW1P4a5LC8Rd
JWLKBIsBR3d0yiZ06D1WqQKBgQCfmsGqMGROTZnig0H8wOb6BMYMfAe8bzvfh4Q9
FiOG928/A5tr6jqzD/Hctk3Etah83nGg6l+gcd+toloqhzlBpuNU8hWB/OCiiYIP
sE5pa0BvPQbodmxzf78w58LuzURydBuZMNEBpFYQdr9KzmuNSn2bZCaJJnDxmOod
FBae8wKBgGjgwEgI+syBCqLSA2LcXrzX3WRLXqSYBT5mW01KIf2ZPkiOugiJHLvs
cjknS3NKSALy5+4QNJ33kKDb39/RCmvj1SiQC2wFz0zXMXVxYZkZBXGuK7P7U2yg
gWsWhlS4pDBTyJLnEOZI+Lid3hsZMXHfbFVuZ2nL9GLK6Xtey4ax
-----END RSA PRIVATE KEY-----
EOL

  cat >/tmp/cccp-jenkins.key.pub <<EOL
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCns8MBPWY2QMsYvURuIprqmiQ/rpJGBS2JhWJA0WlDMUaMGR+pmQ83Se7nXlOyiqLq2ln7UBvoGmXjuTjg69FUb61relflWd9pkT3T3qW0UWMWsxcBwcyJ8oHiuvXbqZuiA1e22psKphqDnFqGCgXH8Pv4d34aVb7BHpi+5LfLbTpZsTksWdtv/kQD6chXPcv8fMVif/avwMYKYNmpfHYgUmgPUx1Ogop/fvSv26cPYn40AsRTOx4yTvPbK4Z0CDJ+VvbLrJjYkeTV6DqMoxskDR/lWaXlA64/lLncEJ6szaDzWY4iN6JKy8PDfr7ThrMwSxuXWcd8mNEMdijnR1vX
EOL

  echo "============================================"
  echo "Creating inventory file at /tmp/hosts.docker"
  echo "============================================"
  echo ""
  local CCCP_INDEX_SOURCE_REPO=$1
  local CCCP_INDEX_SOURCE_BRANCH=$2
  local CCCP_SOURCE_REPO=$3
  local CCCP_SOURCE_BRANCH=$4

  cat >/tmp/hosts.docker <<EOL
[all:children]
jenkins_master
jenkins_slaves
openshift
scanner_worker

[jenkins_master]
192.168.10.10

[sentry]
192.168.10.10

[jenkins_slaves]
192.168.10.20

[openshift]
192.168.10.30

[scanner_worker]
192.168.10.40

[all:vars]
enable_epel= true
ansible_connection=ssh 
ansible_ssh_user=root
ansible_ssh_pass=root
jenkins_admin_username=admin
jenkins_admin_password=admin
public_registry=192.168.10.20
intranet_registry=192.168.10.20:5000
beanstalk_server=192.168.10.30
rsync_ssh_opts="--rsh=/usr/bin/sshpass -p root ssh -o StrictHostKeyChecking=no -l root"
cccp_index_repo=${CCCP_INDEX_SOURCE_REPO}
cccp_index_repo_branch=${CCCP_INDEX_SOURCE_BRANCH}
setup_nfs=False
test=True
copy_ssl_certs=True
test_nfs_share=192.168.10.40:/nfsshare
deployment=docker
log_level = DEBUG
db_backup_host_path=/srv/pipeline-logs/db/cccp/
db_local_volume=/srv/local-db-volume/cccp
db_backup_nfs_path=/srv/db/cccp
db_host=192.168.10.10
allowed_hosts = "['127.0.0.1', '192.168.10.20', '192.168.10.10']"
jenkins_public_key_file=/tmp/cccp-jenkins.key.pub
jenkins_private_key_file=/tmp/cccp-jenkins.key
cccp_source_repo= ${CCCP_SOURCE_REPO}
cccp_source_branch= ${CCCP_SOURCE_BRANCH}
log_level= INFO
db_user= cccp
db_name= cccp
db_pass= cccp
db_host= '192.168.10.10'
db_port= 5432
postgresql_image= registry.centos.org/centos/postgresql-95-centos7
postgresql_uid= 26
expire_tar_after= 4
sentry_enabled= false
sentry_log_level= 'WARNING'
sentry_dsn= ''

[jenkins_master:vars]
oc_slave=192.168.10.20
logrotate_maxsize=100M
logrotate_rotate=5
EOL

  echo "============================================"
  echo "Deploying via Ansible, grab a coffee!       "
  echo "============================================"
  echo ""
  ansible-playbook --skip-tags "selinux" -u root -i /tmp/hosts.docker main.yml

  echo "==================================================================="
  echo "Successfully deployed!"
  echo ""
  echo "Logs are located at ${PWD}/pipeline-logs"
  echo ""
  echo "|--------------------------------------------------------------|"
  echo "| Service   | IP/Host                    | Username/Password   |"
  echo "|--------------------------------------------------------------|"
  echo "| Registry  | https://192.168.10.20      |                     |"
  echo "| Jenkins   | http://192.168.10.10:8080  | admin:admin         |"
  echo "| OpenShift | https://192.168.10.30:8443 | test-admin:test     |"
  echo "|--------------------------------------------------------------|"
  echo "==================================================================="
  echo ""
}


choice=$1

if [[ $choice == "up" ]]; then
  up
elif [[ $choice == "down" ]]; then
  down
elif [[ $choice == "deploy" ]]; then
  deploy ${@:2}
elif [[ $choice == "restart" ]]; then
  up
  down
else
  echo "CCCP Development Setup: Use this to bring up a container-based development setup for CCCP"
  echo ""
  echo "Usage:"
  echo " ./dev [command]"
  echo ""
  echo "Available Commands:"
  echo " up     Brings up 4 SSH-accessible CentOS 7 containers for deployment"
  echo " down   Destroys the four containers"
  echo " deploy Deploys the Ansible provisioning script"
  echo ""
  echo "Deploy:"
  echo " deploy [container-index] [container-index-branch] [cccp] [cccp-branch]"
  echo ""
  echo "Examples:"
  echo " ./dev.sh deploy https://github.com/USERNAME/container-index master https://github.com/USERNAME/container-pipeline test-branch"
fi
