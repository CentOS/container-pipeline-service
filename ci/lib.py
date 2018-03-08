import json
import os
import select
import subprocess
import sys

from time import sleep

from constants import PROJECT_DIR,\
    DEPLOY_LOGS_PATH,\
    JENKINS_HOSTNAME,\
    JENKINS_HTTP_PORT,\
    JENKINS_JAR_LOCATION,\
    CI_TEST_JOB_NAME, \
    CONTROLLER_WORK_DIR, \
    PEP8_CONF


"""
Notes:
    1 - We receive 5 nodes from duffy
        - jenkins master node
        - jenkins slave node
        - openshift node
        - scanner node
        - controller node
    2 - Following is the order in which we assign nodes to roles
        jenkins_master_host = nodes[0]
        jenkins_slave_host = nodes[1]
        openshift_host = nodes[2]
        scanner_host = nodes[3]
        controller = nodes[4]
"""


def _print(msg):
    """
    Custom print function for printing instantly and not waiting on buffer

    Args:
        msg (str): Message to print message on stdout.
    """
    print msg
    sys.stdout.flush()


def run_cmd(cmd, user='root', host=None, private_key='', stream=False):
    """"
    Run the shell command

    Args:
        cmd (str): Shell command to run on the given node.
        user (str): User with which to run command. Defaults to root.
        host (str):
            Host to run command upon, this could be hostname or IP address.
            Defaults to None, which means run command on local host.
        private_key (str):
            private key for the authentication purpose. Defaults to ''.
        stream (bool):
            Whether stream output of command back. Defaults to False.

    Returns:
        str: The output of command.

    Note:
        If stream=True, the function writes to stdout.
    """

    """ # NOTE: Stop printing run command on CI console, uncomment if needed
    _print('=' * 30 + 'RUN COMMAND' + "=" * 30)
    _print({
        'cmd': cmd,
        'user': user,
        'host': host,
        'private_key': private_key,
        'stream': stream
    })
    """
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
    out, err = "", ""
    if stream:
        def read(out, err):
            reads = [p.stdout.fileno(), p.stderr.fileno()]
            ret = select.select(reads, [], [], 0.0)

            for fd in ret[0]:
                if fd == p.stdout.fileno():
                    c = p.stdout.read(1)
                    sys.stdout.write(c)
                    out += c
                if fd == p.stderr.fileno():
                    c = p.stderr.read(1)
                    sys.stderr.write(c)
                    err += c
            return out, err

        while p.poll() is None:
            out, err = read(out, err)

        # Retrieve remaining data from stdout, stderr
        for fd in select.select([p.stdout.fileno(), p.stderr.fileno()],
                                [], [], 0.0)[0]:
            if fd == p.stdout.fileno():
                for c in iter(lambda: p.stdout.read(1), ''):
                    sys.stdout.write(c)
                    out += c
            if fd == p.stderr.fileno():
                for c in iter(lambda: p.stderr.read(1), ''):
                    sys.stderr.write(c)
                    err += c
        sys.stdout.flush()
        sys.stderr.flush()
    else:
        out, err = p.communicate()
    if p.returncode is not None and p.returncode != 0:
        if not stream:
            _print("=" * 30 + "ERROR" + "=" * 30)
            _print('ERROR: %s\nOUT: %s' % (err, out))
        raise Exception('Run Command Error for: %s\n%s' % (_cmd, err))
    return out


class ProvisionHandler(object):
    """
    Handle utilities for provisioning service on CI infrastructure.

    This __init__ method for this class sets object property self._provisioned
    to a bool value. The value is retrieved from envrionment variable
    CCP_CI_PROVISONED during class intialization, if env variable is not found,
    defaults to False.
    """

    def __init__(self):
        self._provisioned = True if os.environ.get(
            'CCCP_CI_PROVISIONED', None) == 'true' else False

    def run(self, controller, force=False, extra_args="", stream=False):
        """
        Run ansible provisioning.

        Args:
            controller (str): Hostname of the controller node.
            force (bool): Whether to provision forcefully. Defaults to False.
            extra_args (str):
                Extra arguments to pass during provisioning.
                Defaults to empty string "".
            stream (bool):
                Whether to stream output of provisioning on stdout.
                Defaults to False.

        Returns:
            tuple:
                (bool, str)
                bool - whether provisioning succeed
                str -  output if any

        """
        if not force and self._provisioned:
            return False, ''

        host = controller.get('host')

        # find work directory to run commands from
        workdir = os.path.expanduser(controller.get('workdir') or '') or \
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)), '../')

        # populate private key for password less ssh access
        private_key = os.path.expanduser(
            controller.get('private_key') or '') if not host else \
            controller.get('private_key')

        # generate private key arguments to be used as is in commands
        private_key_args = (
            '--private-key=%s' % private_key if private_key else '')

        # populate inventory file path
        inventory = os.path.join(workdir, controller.get('inventory_path'))

        # user to run the ansible provisioning with
        user = controller.get('user', 'root')

        # generate the ansible provisioning command
        cmd = (
            "cd {workdir} && "
            "ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i {inventory} "
            "-u {user} {private_key_args} {extra_args} "
            "provisions/main.yml --become-method=sudo --become "
            "> {deploy_logs_path}"
        ).format(workdir=workdir, inventory=inventory, user=user,
                 private_key_args=private_key_args,
                 extra_args=extra_args, deploy_logs_path=DEPLOY_LOGS_PATH)
        _print('Provisioning command: %s' % cmd)

        # run the command
        out = run_cmd(cmd, host=host, stream=stream)

        self._provisioned = True
        return True, out


# alias the run method of class to be used later
provision = ProvisionHandler().run


def generate_ansible_inventory(jenkins_master_host, jenkins_slave_host,
                               openshift_host, scanner_host, nfs_share):
    """Generates ansible inventory text for provisioning nodes.

    Args:
        jenkins_master_host (str): Hostanme of Jenkins master
        jenkins_slave_host (str): Hostname of Jenkins slave
        openshift_host (str): Hostname of OpenShift node
        scanner_host (str): Hostname of scanner node
        nfs_share (str): NFS mount path to be configured on all nodes

    Note:
        This function writes ansible inventory file to "hosts" file
        inside project directory. This inventory is then used for
        provisioning.
    """

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
db_host= {jenkins_master_host}
public_registry= {jenkins_slave_host}
intranet_registry = {jenkins_slave_host}:5000
copy_ssl_certs=True
openshift_startup_delay=150
beanstalk_server={openshift_host}
test=True
jenkins_public_key_file = jenkins.key.pub
enable_epel=False
test_nfs_share={test_nfs_share}
setup_nfs=True
production=False
log_level=DEBUG
openshift_server_ip={openshift_host}
deployment=ci
cccp_index_repo=https://github.com/centos/container-index.git
cccp_index_repo_branch=ci
db_backup_nfs_path=/srv/db/cccp
db_local_volume=/srv/local-db-volume/cccp

[jenkins_master:vars]
jenkins_private_key_file = jenkins.key
oc_slave={jenkins_slave_host}""").format(
        jenkins_master_host=jenkins_master_host,
        jenkins_slave_host=jenkins_slave_host,
        openshift_host=openshift_host,
        scanner_host=scanner_host,
        test_nfs_share=test_nfs_share)

    inventory_export_path = os.path.join(PROJECT_DIR, 'hosts')
    _print("Generating ansible inventory file: %s" % inventory_export_path)
    with open(inventory_export_path, 'w') as f:
        f.write(ansible_inventory)


def setup_ssh_access(from_node, to_nodes):
    """
    Configures password less ssh access

    Args:
        from_node (str): The source node to have ssh access from
        to_nodes (list):
            List of target nodes to configure ssh access from from_node.
    """
    # generate a new key for from_node
    run_cmd('rm -f ~/.ssh/id_rsa* && '
            'ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa',
            host=from_node)

    # get the public key for from_node
    pub_key = run_cmd('cat ~/.ssh/id_rsa.pub', host=from_node).strip()

    # copy the public key of from_node to to_node(s) authorized_keys file
    for node in to_nodes:
        run_cmd(
            'echo "%s" >> ~/.ssh/authorized_keys' % pub_key,
            host=node)


def sync_controller(controller, stream=False):
    """
    Syncs the controller host pipeline service code

    Args:
        controller (str): Hostname of controller node
        strem (bool): Whether to stream output of syncing
    """
    run_cmd(
        "rsync -auvr --delete "
        "-e 'ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no' "
        "%s/ root@%s:%s" % (
            PROJECT_DIR, controller, CONTROLLER_WORK_DIR), stream=stream)


def setup_controller(controller):
    """
    Install needed packages and utilities on controller node

    Args:
        controller (str): Hostname of controller node
    """
    # provision controller node, install required packages
    run_cmd(
        "yum install -y git && "
        "yum install -y rsync && "
        "yum install -y gcc libffi-devel python-devel openssl-devel && "
        "yum install -y epel-release && "
        "yum install -y PyYAML python-networkx python-nose python-pep8 && "
        "yum install -y "
        "http://cbs.centos.org/kojifiles/packages/ansible/2.2.1.0/"
        "2.el7/noarch/ansible-2.2.1.0-2.el7.noarch.rpm",
        host=controller)


def setup(nodes, options):
    """
    Setup CI

    Args:
        nodes (list): List of nodes to setup pipeline service upon
        options (dict):
            Dictionary of additional options to provison service with.
            For example, options{"nfs_share": "/srv/pipeline-logs"}.

    Returns:
        dict:
            Dictionary with details about deployment.
            {
                "provisoned": True,
                "host": {<details about hosts configured>}
            }

    """
    # remove any previously set environment variables
    os.environ.pop('CCCP_CI_PROVISIONED', None)
    os.environ.pop('CCCP_CI_HOSTS', None)

    jenkins_master_host = nodes[0]
    jenkins_slave_host = nodes[1]
    openshift_host = nodes[2]
    scanner_host = nodes[3]
    controller = nodes[4]

    # generate deployment nodes and hostnames text
    nodes_env = (
        "\nJENKINS_MASTER_HOST=%s\n"
        "JENKINS_SLAVE_HOST=%s\n"
        "OPENSHIFT_HOST=%s\n"
        "CONTROLLER=%s\n"
        "SCANNER_HOST=%s\n"
    ) % (jenkins_master_host, jenkins_slave_host,
         openshift_host, controller, scanner_host)

    # export the nodes and hostname details in a file
    with open('env.properties', 'a') as f:
        f.write(nodes_env)

    # Generate hosts_data dict to be printed on CI console
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
        'scanner': {
            'host': scanner_host,
            'remote_user': 'root'
        },
        'controller': {
            'host': controller,
            'user': 'root',
            'workdir': CONTROLLER_WORK_DIR,
            # relative to this workdir
            'inventory_path': 'hosts'
        }
    }

    # prints hosts details on CI console
    _print("=" * 30 + "Hosts data" + "=" * 30 + "\n%s" % hosts_data)

    # generate the needed inventory file for provisioning
    generate_ansible_inventory(jenkins_master_host,
                               jenkins_slave_host,
                               openshift_host,
                               scanner_host,
                               options['nfs_share'])

    # sync controller with service code and patches applied on top
    _print("Sync controler node with ansible inventory file")
    sync_controller(controller)

    # Flush iptables for openshift host
    run_cmd('iptables -F', host=openshift_host)
    # Flush iptables for jenkins slave host
    run_cmd('iptables -F', host=jenkins_slave_host)
    # configure SELinux Permissive mode for openshift host
    run_cmd('setenforce 0', host=openshift_host)

    # setup controller to rest nodes ssh access
    setup_ssh_access(controller, nodes[:-1])

    provision(hosts_data['controller'], stream=True)

    return {
        'provisioned': True,
        'hosts': hosts_data
    }


def run_cccp_index_job(jenkins_master):
    """Run cccp-index job configured in Jenkins

    Running this job on jenkins master populates projects in jenkins.
    The populated projects job details are listed in cccp-index
    pointed by service.
    This function uses java commands and jenkins master end point
    to run the job.

    Args:
        jenkins_master (str): Jenkins master hostname for deployed service

    Raises:
        ExceptionError: If cccp-index job running fails.
    """

    # build command for running cccp-index job
    cmd = ("java -jar {jar_location} -s http://{jenkins_hostname}:{http_port} "
           "build cccp-index -f -v").format(
        jar_location=JENKINS_JAR_LOCATION,
        jenkins_hostname=JENKINS_HOSTNAME,
        http_port=JENKINS_HTTP_PORT
    )
    # run the command store the results to check further
    out = run_cmd(cmd, host=jenkins_master)

    # if there is error in running cccp-index job, fail
    if "Finished:Error" in out:
        raise Exception("Failed running cccp-index job. Exiting!")

    # check if test job is created
    cmd = ("java -jar {jar_location} -s http://{jenkins_hostname}:{http_port} "
           "list-jobs").format(
        jar_location=JENKINS_JAR_LOCATION,
        jenkins_hostname=JENKINS_HOSTNAME,
        http_port=JENKINS_HTTP_PORT
    )
    # retry 50 times with 10 seconds interval
    for i in range(50):
        jenkins_jobs = run_cmd(cmd, host=jenkins_master)
        if CI_TEST_JOB_NAME not in jenkins_jobs:
            # wait for test 10 seconds to let jenkins populate the jobs
            sleep(10)
            continue
        else:
            _print("Test jobs are created successfully!")
            break

    # get the job names in a list
    jenkins_jobs = jenkins_jobs.strip().split()

    # now finally disable the jenkins jobs, since we need one time run only
    cmd = ("java -jar {jar_location} -s http://{jenkins_hostname}:{http_port} "
           " disable-job").format(
        jar_location=JENKINS_JAR_LOCATION,
        jenkins_hostname=JENKINS_HOSTNAME,
        http_port=JENKINS_HTTP_PORT
    )
    # disable the jobs one by one
    for job in jenkins_jobs:
        # append the job name at the end of command and execute
        run_cmd(cmd + " " + job, host=jenkins_master)


def test(data, path=None):
    """
    Run the tests using nosetests

    Args:
        data (dict):
            Details about hosts configured. Output from setup function
        path (str):
            Path of tests directory to run tests.
            Defaults to None

    Note: If explicity path argument is not provided.
    "~/container-pipeline-service/ci/tests" is used.
    """
    path = path or '~/container-pipeline-service/ci/tests'
    hosts_env = json.dumps(data['hosts']).replace('"', '\\"')
    provisioned_env = ('true' if data['provisioned'] else '')

    # get the controller node for run_cmd
    controller = data['hosts']['controller']['host']

    # run the nosetests from controller hosts
    run_cmd(
        'export CCCP_CI_HOSTS="%s" && '
        'export CCCP_CI_PROVISIONED=%s && '
        'nosetests %s' % (
            hosts_env, provisioned_env, path),
        host=controller, stream=True)


def run_pep8_gate(controller):
    """
    Run pep8 on controller node before running actual nodes
    Fails CI if there are pep8 issues with the code

    Args:
        controller: String - hostname for controller node
    """
    # CONTROLLER_WORK_DIR constant is the path where source code
    # on controller is synced at, check constants.py and constant references
    # run pep8 gate on pipeline service code

    _print("Set up controller node with required packages..")
    setup_controller(controller)

    # sync controller with service code and patches applied on top
    _print("Sync controler node with source code..")
    sync_controller(controller)

    _print("Running pep8 checks on source code..")
    run_cmd("cd {0} && pep8 --config {1} . && cd -".format(
        CONTROLLER_WORK_DIR, PEP8_CONF),
        host=controller, stream=True)
    _print("=" * 30 + "PEP8 checks passed!" + "=" * 30)


def teardown():
    pass
