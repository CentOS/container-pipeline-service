# centos-cccp-ansible
Ansible scripts to setup CentOS Community Container Pipeline


## Useful playbook variables

- **cccp_index_repo**: Repository for container index, defaults to ``https://github.com/centos/container-index``. It can be pointed to a fork of or repo similar to the official CentOS container index repo.
- **oc_slave**: Hostname of Openshift Slave machine
- **jenkins_private_key_file**: Path to private key file for Jenkins master
- **jenkins_public_key_file**: Path to public key file for Jenkins slave
- **jenkins_admin_username**: Admin username for Jenkins
- **jenkins_admin_password**: Admin password for Jenkins
- **public_registry**: Endpoint for public container registry
- **nginx_conf_template**: Template name for nginx conf for container registry in ``nginx`` role
- **nginx_conf_file**: Filename for nginx conf for container registry in target node
- **ssl_cert_file**: SSL cert file path in nginx machine
- **ssl_key_file**: SSL key file path in nginx machine
- **copy_ssl_certs**: Copy insecure nginx SSL cert/key files for local setup, when true
- **beanstalk_server**: Hostname of beanstalk server machine
- **vagrant**: Set to ``true`` when provisioning using Vagrant

There are many more playbook variables defined. You can refer to the default
values in the ``defaults/main.yml`` file inside the respective role directories.
