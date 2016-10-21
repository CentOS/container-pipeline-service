import json
import urllib
import subprocess
import os
import sys

url_base = os.environ.get('URL_BASE')
api = os.environ.get('API')
ver = "7"
arch = "x86_64"
count = 4

repo_url = os.environ.get('ghprbAuthorRepoGitUrl') or \
    os.environ.get('GIT_URL')
repo_branch = os.environ.get('ghprbSourceBranch') or \
    os.environ.get('ghprbTargetBranch') or 'master'


def _print(msg):
    print msg
    sys.stdout.flush()


def get_nodes(ver="7", arch="x86_64", count=4):
    get_nodes_url = "%s/Node/get?key=%s&ver=%s&arch=%s&count=%s" % (
        url_base, api, ver, arch, count)

    resp = urllib.urlopen(get_nodes_url).read()
    data = json.loads(resp)
    with open('env.properties', 'a') as f:
        f.write('DUFFY_SSID=%s' % data['ssid'])
        f.close()
    _print(resp)
    return data['hosts']


def run_cmd(cmd, user='root', host=None):
    if host:
        _cmd = (
            "ssh -t -o UserKnownHostsFile=/dev/null -o "
            "StrictHostKeyChecking=no {user}@{host} '"
            "{cmd}"
            "'"
        ).format(user=user, cmd=cmd, host=host)
    else:
        _cmd = cmd
    ret = subprocess.call(_cmd, shell=True)
    if ret != 0:
        raise


def generate_ansible_inventory(jenkins_master_host, jenkins_slave_host,
                               openshift_host, scanner_host):

    ansible_inventory = ("""
[all:children]
jenkins_master
jenkins_slaves
openshift
scanner_worker

[jenkins_master]
{jenkins_master_host}

[jenkins_slaves]
{jenkins_slave_host}

[openshift]
{openshift_host}

[scanner_worker]
{scanner_host}

[all:vars]
public_registry= {jenkins_slave_host}
copy_ssl_certs=true
openshift_startup_delay=150
beanstalk_server={openshift_host}
test=true
cccp_source_repo={repo_url}
cccp_source_branch={repo_branch}
jenkins_public_key_file = jenkins.key.pub

[jenkins_master:vars]
jenkins_private_key_file = jenkins.key
cccp_index_repo=https://github.com/rtnpro/container-index.git
oc_slave={jenkins_slave_host}""").format(
        jenkins_master_host=jenkins_master_host,
        jenkins_slave_host=jenkins_slave_host,
        openshift_host=openshift_host,
        repo_url=repo_url,
        repo_branch=repo_branch,
        scanner_host=scanner_host)

    with open('hosts', 'w') as f:
        f.write(ansible_inventory)


def setup_controller(controller):
    # provision controller
    run_cmd(
        "scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no "
        "~/.ssh/id_rsa root@%s:/root/.ssh/id_rsa" % controller
    )

    run_cmd(
        "yum install -y git epel-release && "
        "yum install -y ansible python2-jenkins-job-builder",
        host=controller)

    run_cmd(
        "scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -r "
        "./ root@%s:/root/container-pipeline-service" % controller)


def provision(controller):
    run_cmd(
        "cd /root/container-pipeline-service && "
        "ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i hosts -u root "
        "--private-key=/root/.ssh/id_rsa provisions/vagrant.yml",
        host=controller)
