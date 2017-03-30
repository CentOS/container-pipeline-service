import subprocess
import os
import sys
import json

PROJECT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__),
                 '..')
)


def _print(msg):
    print msg
    sys.stdout.flush()


def run_cmd(cmd, user='root', host=None, private_key='', stream=False):
    _print('=' * 30 + 'RUN COMMAND' + "=" * 30)
    _print({
        'cmd': cmd,
        'user': user,
        'host': host,
        'private_key': private_key,
        'stream': stream
    })
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
    out = ""
    if stream:
        for line in iter(p.stdout.readline, ''):
            _print(line.strip())
            out += line
    _out, err = p.communicate()
    out += _out or ""
    if p.returncode is not None and p.returncode != 0:
        _print("=" * 30 + "ERROR" + "=" * 30)
        _print(err)
        raise Exception(err)
    return out


class ProvisionHandler(object):

    def __init__(self):
        self._provisioned = True if os.environ.get(
            'CCCP_CI_PROVISIONED', None) == 'true' else False

    def run(self, controller, force=False, extra_args=""):
        if not force and self._provisioned:
            return

        host = controller.get('host')

        workdir = os.path.expanduser(controller.get('workdir') or '') or \
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)), '../')
        private_key = os.path.expanduser(
            controller.get('private_key') or '') if not host else \
            controller.get('private_key')

        private_key_args = (
            '--private-key=%s' % private_key if private_key else '')

        inventory = os.path.join(workdir, controller.get('inventory_path'))
        user = controller.get('user', 'root')
        cmd = (
            "cd {workdir} && "
            "ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i {inventory} "
            "-u {user} -s {private_key_args} {extra_args} "
            "provisions/vagrant.yml"
        ).format(workdir=workdir, inventory=inventory, user=user,
                 private_key_args=private_key_args,
                 extra_args=extra_args)
        _print('Provisioning command: %s' % cmd)
        run_cmd(cmd, host=host, stream=True)
        self._provisioned = True

provision = ProvisionHandler().run


def generate_ansible_inventory(jenkins_master_host, jenkins_slave_host,
                               openshift_host, scanner_host, nfs_share):

    test_nfs_share = scanner_host + ":" + nfs_share

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
copy_ssl_certs=True
openshift_startup_delay=150
beanstalk_server={openshift_host}
test=True
jenkins_public_key_file = jenkins.key.pub
enable_epel=False
test_nfs_share={test_nfs_share}

[jenkins_master:vars]
jenkins_private_key_file = jenkins.key
cccp_index_repo=https://github.com/rtnpro/container-index.git
oc_slave={jenkins_slave_host}""").format(
        jenkins_master_host=jenkins_master_host,
        jenkins_slave_host=jenkins_slave_host,
        openshift_host=openshift_host,
        scanner_host=scanner_host,
        test_nfs_share=test_nfs_share)

    with open(os.path.join(PROJECT_DIR, 'hosts'), 'w') as f:
        f.write(ansible_inventory)

    print test_nfs_share


def setup_ssh_access(from_node, to_nodes):
    run_cmd('rm -f ~/.ssh/id_rsa* && '
            'ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa',
            host=from_node)
    pub_key = run_cmd('cat ~/.ssh/id_rsa.pub', host=from_node).strip()
    for node in to_nodes:
        run_cmd(
            'echo "%s" >> ~/.ssh/authorized_keys' % pub_key,
            host=node)


def sync_controller(controller, stream=False):
    run_cmd(
        "rsync -auvr --delete "
        "-e 'ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no' "
        "%s/ root@%s:/root/container-pipeline-service" % (
            PROJECT_DIR, controller), stream=stream)


def setup_controller(controller):
    # provision controller
    run_cmd(
        "yum install -y git && "
        "yum install -y python-virtualenv && "
        "yum install -y gcc libffi-devel python-devel openssl-devel && "
        "virtualenv venv && "
        "$HOME/venv/bin/pip install ansible==2.2.1 && "
        "ln -s $HOME/venv/bin/ansible-playbook /usr/bin/ansible-playbook || "
        "true && "
        "$HOME/venv/bin/pip install nose && "
        "ln -s $HOME/venv/bin/nosetests /usr/bin/nosetests || true",
        host=controller)


def setup(nodes, options):
    os.environ.pop('CCCP_CI_PROVISIONED', None)
    os.environ.pop('CCCP_CI_HOSTS', None)

    jenkins_master_host = nodes[0]
    jenkins_slave_host = nodes[1]
    openshift_host = nodes[2]
    scanner_host = nodes[3]
    controller = nodes.pop()

    nodes_env = (
        "\nJENKINS_MASTER_HOST=%s\n"
        "JENKINS_SLAVE_HOST=%s\n"
        "OPENSHIFT_HOST=%s\n"
        "CONTROLLER=%s\n"
        "SCANNER_HOST=%s\n"
    ) % (jenkins_master_host, jenkins_slave_host,
         openshift_host, controller, scanner_host)

    with open('env.properties', 'a') as f:
        f.write(nodes_env)

    hosts_data = {
        'openshift': {
            'host': openshift_host,
            'remote_user': 'root'
        },
        'jenkins_master': {
            'host': jenkins_master_host,
            'remote_user': 'root'
        },
        'jenkins_slave': {
            'host': jenkins_slave_host,
            'remote_user': 'root'
        },
        'controller': {
            'host': controller,
            'user': 'root',
            'workdir': '/root/container-pipeline-service',
            # relative to this workdir
            'inventory_path': 'hosts'
        }
    }

    _print(hosts_data)

    generate_ansible_inventory(jenkins_master_host,
                               jenkins_slave_host,
                               openshift_host,
                               scanner_host,
                               options['nfs_share'])

    run_cmd('iptables -F', host=openshift_host)
    run_cmd('iptables -F', host=jenkins_slave_host)
    run_cmd('setenforce 0', host=openshift_host)

    setup_ssh_access(controller, nodes + [controller])
    sync_controller(controller)
    setup_controller(controller)

    provision(hosts_data['controller'])

    return {
        'provisioned': True,
        'hosts': hosts_data
    }


def test(data, path):
    path = path or '~/container-pipeline-service/ci/tests'
    hosts_env = json.dumps(data['hosts']).replace('"', '\\"')
    provisioned_env = ('true' if data['provisioned'] else '')
    controller = data['hosts']['controller']['host']
    run_cmd(
        'export CCCP_CI_HOSTS="%s" && '
        'export CCCP_CI_PROVISIONED=%s && '
        'nosetests %s' % (
            hosts_env, provisioned_env, path),
        host=controller, stream=True)


def teardown():
    pass
