**This document describes the steps to be followed to upgrade OpenShift cluster
setup done using [cluster-install](cluster-install.md). It will help do an
upgrade from OpenShift 3.7.2 to OpenShift 3.9.0.**

Steps mentioned below help you do a rolling, full system restarts of the hosts
used to deploy the OpenShift cluster. Add the variable
`openshift_rolling_restart_mode` to the hosts file. Here's an example of the
hosts file we used to upgrade the cluster from 3.7.2 to 3.9.0:

```
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
openshift_release=v3.9
os_firewall_use_firewalld=true
openshift_clock_enabled=false
openshift_pkg_version=-3.9.0
openshift_enable_service_catalog=false
openshift_docker_insecure_registries=172.29.33.8:5000
openshift_docker_additional_registries=172.29.33.8:5000
openshift_master_default_subdomain={{ hostvars[groups['masters'][0]].openshift_ip }}.nip.io
openshift_rolling_restart_mode=system

# uncomment the following to enable htpasswd authentication; defaults to DenyAllPasswordIdentityProvider
openshift_master_identity_providers=[{'name': 'htpasswd_auth', 'login': 'true', 'challenge': 'true', 'kind': 'HTPasswdPasswordIdentityProvider', 'filename': '/etc/origin/master/htpasswd'}]

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
os-master-1.lon1.centos.org openshift_node_labels="{'region': 'infra','zone': 'default','purpose':'infra', 'node-type': 'logging'}" openshift_schedulable=true openshift_ip=172.29.33.53
os-master-2.lon1.centos.org openshift_node_labels="{'region': 'infra','zone': 'default','purpose':'infra', 'node-type': 'logging'}" openshift_schedulable=true openshift_ip=172.29.33.46
os-node-1.lon1.centos.org openshift_node_labels="{'region':'primary','zone': 'default','purpose':'prod', 'node-type': 'logging'}" openshift_schedulable=true openshift_ip=172.29.33.58
os-node-2.lon1.centos.org openshift_node_labels="{'region':'primary','zone': 'default','purpose':'prod', 'node-type': 'logging'}" openshift_schedulable=true openshift_ip=172.29.33.42
```

Make sure to replace `openshift_ip` with relevant IP addresses in your cluster.

Since we're using `openshift-ansible` from CentOS repos, we have to make sure
that the package installed in the Ansible controller system is for 3.9. If you
followed [cluster-install](cluster-install.md) doc, you likely have packages
installed for 3.7.2. Let's remove the 3.7.2 packages and install those for
3.9.0:

```bash
$ yum remove -y centos-release-openshift-origin37.noarch openshift-ansible

$ yum install -y centos-release-openshift-origin39.noarch && yum install -y openshift-ansible
```

With this in place, execute the following command:

```bash
$ time ansible-playbook -i openshift-cluster/hosts.39 /usr/share/ansible/openshift-ansible/playbooks/byo/openshift-cluster/upgrades/v3_9/upgrade.yml -vvv
```

Above command will perform upgrade in the cluster. Playbook will take care of
restarting the nodes for us as well. Depending on the network and hardware on
your side, time taken by above command might vary. It took 45 minutes when
executed in [CentOS DevCloud](https://wiki.centos.org/DevCloud) infrastructure.
