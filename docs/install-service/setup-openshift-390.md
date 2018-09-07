# Setup on Openshift Origin 3.9

**This document describes the steps to be followed to bring up a multi-master
and multi-node (2 masters, 2 nodes) OpenShift cluster based on RPM installation**

## Setup the nodes

Bring up 5 nodes (including the Ansible controller, 2 for master and 2 for slave)

### [CentOS DevCloud](https://wiki.centos.org/DevCloud)

A separate system is expected to be reserved as Ansible Controller node from
which we will perform the installation of the cluster. A system similar to
[medium sized VM on CentOS
DevCloud](https://wiki.centos.org/DevCloud#head-6d6f4a2e0275c13dc6ef8b17e73cf64911a97d50) should suffice.

Now, we need to bring up 2 masters and 2 nodes. If you're using DevCloud, below
script should bring up the systems and copy SSH public key of Ansible
controller VM to these new VMs. Make sure that jump host (in DevCloud) or the
system you use to spin up VMs has the script `~/bin/script.sh` with following
contents:

```bash

$ cat ~/bin/script.sh 
sudo bash -c 'echo "<SSH public key of Ansible controller host>" >> ~/.ssh/authorized_keys'

$ cat ~/bin/os_cluster.sh 
#!/bin/bash

echo "" !> ~/.ssh/known_hosts

echo -n "Removing old environment..."
openstack server delete --wait os-master-1 && echo "Successfully deleted os-master-1" || echo "os-master-1 does not exist"
openstack server delete --wait os-master-2 && echo "Successfully deleted os-master-2" || echo "os-master-2 does not exist"
openstack server delete --wait os-node-1 && echo "Successfully deleted os-node-1" || echo "os-node-1 does not exist"
openstack server delete --wait os-node-2 && echo "Successfully deleted os-node-2" || echo "os-node-2 does not exist"

echo -n "Creating new environment..."
openstack server create --wait --image 'centos_7' --flavor large_eph60 --key-name ${USER}_key --nic net-id=$(openstack network list -f value |awk '{print $1}') os-master-1
openstack server create --wait --image 'centos_7' --flavor large_eph60 --key-name ${USER}_key --nic net-id=$(openstack network list -f value |awk '{print $1}') os-master-2
openstack server create --wait --image 'centos_7' --flavor large_eph60 --key-name ${USER}_key --nic net-id=$(openstack network list -f value |awk '{print $1}') os-node-1
openstack server create --wait --image 'centos_7' --flavor large_eph60 --key-name ${USER}_key --nic net-id=$(openstack network list -f value |awk '{print $1}') os-node-2

sleep 10

echo -n "Copying ssh keys to new VMs...\n"
op1_ip=`openstack server show os-master-1 -c addresses| awk '/publicnet/ {print $4}' | awk -F'=' '{print $2}'`
op2_ip=`openstack server show os-master-2 -c addresses| awk '/publicnet/ {print $4}' | awk -F'=' '{print $2}'`
op3_ip=`openstack server show os-node-1 -c addresses| awk '/publicnet/ {print $4}' | awk -F'=' '{print $2}'`
op4_ip=`openstack server show os-node-2 -c addresses| awk '/publicnet/ {print $4}' | awk -F'=' '{print $2}'`

scp ~/bin/script.sh centos@$op1_ip:
scp ~/bin/script.sh centos@$op2_ip:
scp ~/bin/script.sh centos@$op3_ip:
scp ~/bin/script.sh centos@$op4_ip:

ssh -t centos@$op1_ip "sh script.sh"
ssh -t centos@$op2_ip "sh script.sh"
ssh -t centos@$op3_ip "sh script.sh"
ssh -t centos@$op4_ip "sh script.sh"
```


### Other Infrastructure

Please make sure you have nodes as expected above one Ansible controller and 4 nodes 2 masters and 2 nodes.

## Setup NFS Storage

Now the systems are ready. We need to create one more system in the infra for
NFS storage to be used by Jenkins and container registry. If you're in a
different infrastructure and your administrator can provide you with access to
NFS storage, you might skip this step and modify things accordingly at a later
stage. A system with configuration similar to small ephemeral (`small_eph60`
flavor) should suffice.

Once the system is ready, use the 60 GB disk space to setup an LVM that can be
used for Jenkins and registry. Execute these steps:

```bash
$ yum install -y lvm2
$ yum update -y
$ umount /mnt
$ pvcreate /dev/vdb
$ vgcreate /dev/vdb
$ vgcreate nfs /dev/vdb
$ lvcreate -L 5G -n jenkins -v nfs
$ mkfs.ext4 /dev/nfs/jenkins

$ cat /etc/fstab
UUID=0356e691-d6fb-4f8b-a905-4230dbe62a32 /                       xfs     defaults        0 0
/dev/nfs/jenkins	/jenkins	ext4	defaults,nofail,comment=cloudconfig	0	2

$ cat /etc/exports
/jenkins *(rw,sync,no_subtree_check,all_squash,anonuid=0,anongid=0)

$ systemctl enable --now nfs-server
```

Similarly, we setup Docker registry on a remote system and use an LVM volume
from earlier created volume group as its storage backend:

```bash
$ lvcreate -L 10G -n registry -v nfs
$ mkfs.ext4 /dev/nfs/registry

$ cat /etc/fstab
UUID=0356e691-d6fb-4f8b-a905-4230dbe62a32 /                       xfs     defaults        0 0
/dev/nfs/jenkins        /jenkins        ext4    defaults,nofail,comment=cloudconfig     0       2
/dev/nfs/registry       /var/lib/registry       ext4    defaults,nofail,comment=cloudconfig     0       2

$ mount -a

$ yum install -y docker-distribution
$ systemctl enable --now docker-distribution
```

Once the VMs are properly setup and NFS is exported, it’s time to setup the cluster.

## Setup Ansible Controller

Please ensure atleast ansible 2.4.3 is installed. In case of CentOS 7 nodes, 2.4.3 is not available in default repositories, but you may install and install openshift-ansible RPM on Ansible controller VM. 

```bash
$ yum install http://cbs.centos.org/kojifiles/packages/ansible/2.4.3.0/1.el7/noarch/ansible-2.4.3.0-1.el7.noarch.rpm
$ yum install centos-release-openshift-origin39.noarch
$ yum install openshift-ansible
```

Now on Ansible controller VM and the two nodes being used to bring up the cluster,
make sure that the `/etc/hosts` file has proper entries of the hosts you’re
going to setup the cluster on. For example, here’s the `/etc/hosts` file on all
five nodes:

```bash
$ cat /etc/hosts
127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
::1         localhost localhost.localdomain localhost6 localhost6.localdomain6

172.29.33.32    os-node-2.lon1.centos.org osn2
172.29.33.36    os-node-1.lon1.centos.org osn1
172.29.33.46    os-master-2.lon1.centos.org osm2
172.29.33.38    os-master-1.lon1.centos.org osm1
```

One of the next steps in the guide will automatically copy this file from
Ansible controller VM to all the 4 nodes of cluster. So just make sure that
your Ansible controller VM has proper entries in `/etc/hosts`.

We will use below Ansible hosts file to bring up the OpenShift cluster:

```
$ cat hosts
# Create an OSEv3 group that contains the masters and nodes groups
[OSEv3:children]
masters
nodes
etcd

# Set variables common for all OSEv3 hosts
[OSEv3:vars]
# SSH user, this user should allow ssh based auth without requiring a password
ansible_ssh_user=root

# If ansible_ssh_user is not root, ansible_become must be set to true
# ansible_become=true
# containerized=true
debug_level=4

openshift_master_api_port=8443
# openshift_master_console_port=8756
openshift_deployment_type=origin
openshift_release=v3.7
os_firewall_use_firewalld=true
openshift_clock_enabled=false
openshift_pkg_version=-3.7.2
openshift_enable_service_catalog=false
openshift_docker_insecure_registries=172.29.33.8:5000
openshift_docker_additional_registries=172.29.33.8:5000
openshift_master_default_subdomain={{ hostvars[groups['masters'][0]].openshift_ip }}.nip.io

# uncomment the following to enable htpasswd authentication; defaults to DenyAllPasswordIdentityProvider
openshift_master_identity_providers=[{'name': 'htpasswd_auth', 'login': 'true', 'challenge': 'true', 'kind': 'HTPasswdPasswordIdentityProvider', 'filename': '/etc/origin/master/htpasswd'}]

# openshift_hosted_logging_deploy=true
# openshift_logging_install_logging=true

# default selectors for router and registry services
openshift_router_selector='region=infra'
openshift_registry_selector='region=infra'
openshift_disable_check=docker_storage,memory_availability

# host group for masters
[masters]
os-master-[1:2].lon1.centos.org

# host group for etcd
[etcd]
os-node-[1:2].lon1.centos.org

# host group for nodes, includes region info
[nodes]
os-master-1.lon1.centos.org openshift_node_labels="{'region': 'infra','zone': 'default','purpose':'infra'}" openshift_schedulable=true openshift_ip=172.29.33.38
os-master-2.lon1.centos.org openshift_node_labels="{'region': 'infra','zone': 'default','purpose':'infra'}" openshift_schedulable=true openshift_ip=172.29.33.46
os-node-1.lon1.centos.org openshift_node_labels="{'region':'primary','zone': 'default','purpose':'prod'}" openshift_schedulable=true openshift_ip=172.29.33.36
os-node-2.lon1.centos.org openshift_node_labels="{'region':'primary','zone': 'default','purpose':'prod'}" openshift_schedulable=true openshift_ip=172.29.33.32
```
## Setting up the cluster

Now, we will perform some pre-install steps that will setup these nodes for
OpenShift installation. Use the following Ansible inventory file:

```yaml
---
- hosts: all
  tasks:
      - name: yum update all
        yum: name='*' state=latest
        async: 1000
        poll: 5

      - name: reboot the server
        shell: sleep 2 && shutdown -r now
        async: 1
        poll: 0

      - name: Wait for server come back
        wait_for: >
             host={{ inventory_hostname }}
             port=22
             delay=15
             timeout=600
        delegate_to: localhost

      - name: Copy /etc/hosts
        synchronize: src=/etc/hosts dest=/etc/hosts
        delegate_to: localhost

      - name: SELinux permissive
        selinux: policy=targeted state=permissive

      - name: Install packages
        yum: package={{ item }} state=latest
        with_items:
            - NetworkManager
            - firewalld
            - python-rhsm-certificates
            - centos-release-openshift-origin39.noarch
            - python-ipaddress

      - name: Start serices
        systemd: state=started enabled=yes name={{ item }}
        with_items:
            - NetworkManager
            - firewalld

      - name: Check if /dev/vdb is mounted on /mnt
        shell: df -h | grep mnt
        register: dfh
        ignore_errors: True

      - name: Run shell commands to use /dev/vdb for /var
        shell: |
            umount /mnt
            wipefs -o 0x52 /dev/vdb
            wipefs -o 0x0 /dev/vdb
            wipefs -o 0x1fe /dev/vdb
            mkfs.ext4 /dev/vdb
            mount /dev/vdb /mnt
            rsync -aqxP /var/* /mnt
            sed -i 's/mnt/var/' /etc/fstab
        when: dfh.rc==0

      - name: Reboot nodes
        shell: reboot
        when: dfh.rc==0
```

Run the pre-install tasks with:

```bash
$ ansible-playbook -i hosts pre-install.yml
```

Last step in above playbook is to reboot the nodes because:
- We are assuming that yum update would have some kernel update and it’s OK to
  restart the nodes before anything’s setup on them.
- We want to make sure that mount point entry in `/etc/fstab` file is working
  as expected.

Now we do the actual OpenShift cluster installation. Start the cluster installation with this
command. I prefer to time it so that I get a rough idea about how long the cluster setup
took:

```bash
$ time ansible-playbook -i hosts /usr/share/ansible/openshift-ansible/playbooks/deploy_cluster.yml -vvv
```

Once the cluster is setup, we need to bring up a Jenkins server using the jenkins
persistent template available in the `openshift` namespace. But we need to perform a
few steps before that. We need to:
- Create a user that’s able to use the OpenShift web console (on openshift master):
  ```bash
  $ oc login -u system:admin --config ~/.kube/config
  $ oc create user cccp
  $ htpasswd /etc/origin/master/htpasswd cccp
  ```

- Create a project:
  ```bash
  # create cccp project using cccp user
  $ oc login -u cccp
  $ oc new-project cccp
  ```

- Create a PV using the 5GB NFS share we created earlier. This can be done only
  as a cluster-admin user. Replace NFS VM IP address to correct one in
  following yml template:
  ```bash
  $ cat jenkins-pv.yml
  apiVersion: v1
  kind: PersistentVolume
  metadata:
  name: jenkins
  namespace: cccp
  spec:
  capacity:
  storage: 5Gi
  accessModes:
  - ReadWriteOnce
  nfs:
  path: /jenkins
  server: 172.29.33.8
  persistentVolumeReclaimPolicy: Recycle

  $ oc login -u system:admin --config ~/.kube/config

  $ oc create -f jenkins-pv.yml
  ```
- Bring up a Jenkins server using the jenkins persistent template. This has to
  be done as normal user and not as admin user. ​ Make sure that the
  Jenkins PV you created in above step is formated/emptied. ​ I spent about
  2 days trying to debug issues arising out of stale data on that NFS storage.
  Also add an extra environment variable to make sure that parallel builds work
  as expected:

  ```bash
  $ oc login -u cccp
  $ oc process -p MEMORY_LIMIT=1Gi openshift//jenkins-persistent | oc create -f -

  # add env var for parallel builds
  $ oc set env dc/jenkins JENKINS_JAVA_OVERRIDES="-Dhudson.slaves.NodeProvisioner.initialDelay=0,-Dhudson.slaves.NodeProvisioner.MARGIN=50,-Dhudson.slaves.NodeProvisioner.MARGIN0=0.85"

  # add required permissions
  $ oc login -u system:admin$ oc adm policy add-scc-to-user privilegedsystem:serviceaccount:cccp:jenkins
  $ oc adm policy add-role-to-user system:image-buildersystem:serviceaccount:cccp:jenkins
  ```

Now go to the OpenShift web console and check if Jenkins deployment has come up
and if the PVC of that deployment is bound to the PV you created earlier.

To access Jenkins web console, you’ll need to check the OpenShift web console for the
route that was created with nip.io subdomain. This should be visible on the
project/namespace’s homepage on OpenShift console.

Configuring DaemonSet: Scanning is one of the build pipeline phase the service
offers. In scanning, we introspect the image built. In order to make scanning
module available on all the possible builder nodes, we configure and deploy
DaemonSet. The DeamonSet spins up a pod per builder node, which avails a docker
volume for all the containers on the node. The scan stage in pipeline uses the
volume for performing scan phase. DaemonSet needs to be deployed using cluster
admin. Configure it with cluster admin user:

```bash
$ git clone https://github.com/dharmit/ccp-openshift
$ cd ccp-openshift
$ oc login -u system:admin
$ oc create -f daemon-set/scan_data.yaml
```

Note: The labels defined for DaemonSet are used in pipeline seed-job/template.yaml
to identify the container created using DaemonSet. Please keep the labels
intact in DaemonSet template.

Finally create the Jenkins Pipeline build to parse the container-index. This will create a
seed-job which will parse the container index and create more Jenkins Pipeline builds
that will create the actual container images for projects covered in the index. Replace
172.29.33.8 with the IP address of your remote registry (you need to configure external
registry by yourself, you can use the NFS VM created for same). Replace  master with the branch you’d like to deploy.

```bash
$ oc process -p PIPELINE_REPO=${PIPELINE_REPO} -p PIPELINE_BRANCH=${PIPELINE_BRANCH} -p REGISTRY_URL=${REGISTRY_URL} -p NAMESPACE=`oc project -q` -f seed-job/buildtemplate.yaml | oc create -f -
```
