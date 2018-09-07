# Setup Logging on Openshift Origin 3.9 Cluster of Service

**This document discusses setting up logging infrastructure in the OpenShift
cluster. It assumes that you have an OpenShift 3.9 cluster already setup.**

 If you don't have an OpenShift 3.9 cluster setup already, you can refer the installation guide [setup-openshift-372.md](setup-openshift-372.md) to install a 3.9 cluster or if you have a 3.7 cluster use [upgrade-372-390.md](../upgrade-openshift/upgrade-372-390.md) to *upgrade* OpenShift 3.9 cluster.

Logging infrastructure that we're going to setup in our cluster is going to be
based on EFK (Elasitcsearch - Fluentd - Kibana). OpenShift has this integrated
and all we need to do is make sure that certain prerequisites are satisfied.
Below are the prerequisites that we took care of before executing the playbook:

- Create a `/logging` directory that's backed by a block storage device of
  reasonable size. We used nearly 35GB for it.
- At the moment, we are using worst possible Linux file persmissions so that
  Elasticsearch pods can access the `/logging` directory:
   
  ```bash
  $ chmod 777 /logging
  ```

Once the cluster is installed, add logging related parameters to the hosts file
so that it looks like below:

```bash
$ cat openshift-cluser/hosts.39
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

# logging stack
openshift_logging_install_logging=true
openshift_logging_es_cluster_size=1
openshift_logging_es_memory_limit=2G
openshift_logging_elasticsearch_storage_type="hostmount"
openshift_logging_elasticsearch_hostmount_path="/logging"
openshift_logging_elasticsearch_nodeselector={'node-type': 'logging'}

# logging stack for ops
openshift_logging_use_ops=true
openshift_logging_es_ops_cluster_size=1
openshift_logging_es_ops_memory_limit=2G

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
os-master-1.lon1.centos.org openshift_node_labels="{'region': 'infra','zone': 'default','purpose':'infra', 'node-type': 'logging'}" openshift_schedulable=true openshift_ip=172.29.33.36
os-master-2.lon1.centos.org openshift_node_labels="{'region': 'infra','zone': 'default','purpose':'infra', 'node-type': 'logging'}" openshift_schedulable=true openshift_ip=172.29.33.46
os-node-1.lon1.centos.org openshift_node_labels="{'region':'primary','zone': 'default','purpose':'prod', 'node-type': 'logging'}" openshift_schedulable=true openshift_ip=172.29.33.23
os-node-2.lon1.centos.org openshift_node_labels="{'region':'primary','zone': 'default','purpose':'prod', 'node-type': 'logging'}" openshift_schedulable=true openshift_ip=172.29.33.52
```

We are setting up two logging stacks. Both the stacks are based on EFK
(Elasticsearch - Fluentd - Kibana). First stack is defined by:

```
# logging stack
openshift_logging_install_logging=true
openshift_logging_es_cluster_size=1
openshift_logging_es_memory_limit=2G
openshift_logging_elasticsearch_storage_type="hostmount"
openshift_logging_elasticsearch_hostmount_path="/logging"
openshift_logging_elasticsearch_nodeselector={'node-type': 'logging'}
```

This is going to use the local host directory on a node which is labeled with
`'node-type': 'logging'` which in case is all the nodes in the cluster. What
this does is spin up EFK stack and use `/logging` directory from one of the
nodes satisfying the mentioned label. 

```
# logging stack for ops
openshift_logging_use_ops=true
openshift_logging_es_ops_cluster_size=1
openshift_logging_es_ops_memory_limit=2G
```

This is again going to use `/logging` directory in one of the nodes with
correct label. It's going to spin up pods for Elasticsearch and Kibana while
single Fluentd pod in the logging namespace is going to take care of sending
logs to the relevant cluster.

Also the Elasticsearch service account needs to be added to `privileged`
scc (security context constraint) so that it can use a `hostPath` mount option:

```bash
$ oc adm policy add-scc-to-user privileged system:serviceaccount:logging:aggregated-logging-elasticsearch
```

Once these things are taken care of, trigger the logging installation using:

```bash
$ time ansible-playbook -i openshift-cluster/hosts.39 /usr/share/ansible/openshift-ansible/playbooks/openshift-logging/config.yml -vvv
```

This will setup both the clusters under `logging` namespace in OpenShift
cluster. If you would like to access `logging` namespace as a regular user in
OpenShift Web Console, you will need to grant `admin` privileges for the user
you login to the console as. For example, you login to the OpenShift Web
Console as developer user, you need to execute below as `system:admin` user:

```bash
$ oc adm policy add-role-to-user admin developer -n logging
```

Now you can view and modify things in the `logging` namepsace in the OpenShift
cluster.

To be able to see the logs in Kibana from EFK Ops deployment, you need to add
`cluster-reader` privileges to the user you're accessing the OpenShift Web
Console with. Going with the developer example mentioned earlier, execute this
command as `system:admin` user to grant the privileges:

```bash
$ oc adm policy add-cluster-role-to-user cluster-reader developer
```

Link to Kibana dashboards is available in OpenShift Web Console under the
respective deployments. Open the web console and go to the logging namespace.
In the Overview page, you'll see the numerous deployments made under the
project. Click on the ones for Kibana and you'll find the link to the route
that exposes this services.
