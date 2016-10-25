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

# env values: ci, vagrant
env = os.environ.get('ENV', 'ci')

repo_url = os.environ.get('ghprbAuthorRepoGitUrl') or \
    os.environ.get('GIT_URL')
repo_branch = os.environ.get('ghprbSourceBranch') or \
    os.environ.get('ghprbTargetBranch') or 'master'


def _print(msg):
    print msg
    sys.stdout.flush()


def run_cmd(cmd, user='root', host=None, private_key='', stream=False):
    if host:
        private_key_args = ''
        if private_key:
            private_key_args = '-i {path}'.format(
                path=os.path.expanduser(private_key))
        _cmd = (
            "ssh -t -o UserKnownHostsFile=/dev/null -o "
            "StrictHostKeyChecking=no {private_key_args} {user}@{host} '"
            "{cmd}"
            "'"
        ).format(user=user, cmd=cmd, host=host,
                 private_key_args=private_key_args)
    else:
        _cmd = cmd

    p = subprocess.Popen(_cmd, shell=True,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    if stream:
        out = ""
        for line in iter(p.stdout.readline, ''):
            _print(line.strip())
            out += line
        if p.returncode != 0:
            raise Exception()
    else:
        out, err = p.communicate()
        if p.returncode != 0:
            raise Exception(err)
    return out


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


class ProvisionHandler(object):

    def __init__(self):
        self._provisioned = False

    def run(self, controller, force=False):
        if not force and self._provisioned:
            return

        workdir = os.path.expanduser(controller.get('workdir') or '') or \
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)), '../')

        private_key = (
            os.path.expanduser(controller.get('private_key') or '') or
            os.path.expanduser('~/.ssh/id_rsa')
        )
        inventory = os.path.join(workdir, controller.get('inventory_path'))
        user = controller.get('user', 'root')
        cmd = (
            "cd {workdir} && "
            "ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i {inventory} "
            "-u {user} -s --private-key={private_key} provisions/vagrant.yml"
        ).format(workdir=workdir, inventory=inventory, user=user,
                 private_key=private_key)
        run_cmd(cmd, host=controller.get('host'), stream=True)
        self._provisioned = True

provision = ProvisionHandler().run
