# This script uses the Duffy node management api to get fresh machines to run
# your CI tests on. Once allocated you will be able to ssh into that machine
# as the root user and setup the environ
#
# XXX: You need to add your own api key below, and also set the right cmd= line
#      needed to run the tests
#
# Please note, this is a basic script, there is no error handling and there are
# no real tests for any exceptions. Patches welcome!

import json
import urllib
import subprocess
import os
import time
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


def test_if_openshift_builds_are_complete(host):
    print "=" * 30
    print "Test if openshift builds are running"
    print "=" * 30
    cmd = (
        "oc login https://openshift:8443 --insecure-skip-tls-verify=true "
        "-u test-admin -p test > /dev/null && "
        "oc project bamachrn-python > /dev/null && "
        "oc get pods"
    )
    _cmd = (
        "ssh -t -o UserKnownHostsFile=/dev/null -o "
        "StrictHostKeyChecking=no {user}@{host} "
        "'{cmd}'"
    ).format(user='root', cmd=cmd, host=host)
    retries = 0
    success = False
    while retries < 10 and success is False:
        if retries > 0:
            time.sleep(60)
        _print("Retries: %d/100" % retries)
        try:
            output = subprocess.check_output(_cmd, shell=True)
            _print(output)
            lines = output.splitlines()
            pods = set([line.split()[0] for line in lines[1:]
                        if line and line.split()[2] == 'Completed'])
            success = not set(
                # FIXME: we're ignoring delivery build right now as it will
                # need the atomic scan host for that.
                # ['build-1-build', 'delivery-1-build', 'test-1-build'])
                ['build-1-build', 'test-1-build', 'delivery-1-build']
            ).difference(pods)
        except subprocess.CalledProcessError:
            success = False
        retries += 1
    if success is False:
        raise Exception("Openshift builds did not complete.")
    _print("Openshift builds completed successfully.")


def test_if_openshift_builds_persist(host):
    _print("=" * 30)
    _print("Test if openshift builds persist after reprovision")
    _print("=" * 30)
    cmd = (
        "oc login https://openshift:8443 --insecure-skip-tls-verify=true "
        "-u test-admin -p test > /dev/null && "
        "oc project bamachrn-python > /dev/null && "
        "oc get pods"
    )
    _cmd = (
        "ssh -t -o UserKnownHostsFile=/dev/null -o "
        "StrictHostKeyChecking=no {user}@{host} "
        "'{cmd}'"
    ).format(user='root', cmd=cmd, host=host)
    output = subprocess.check_output(_cmd, shell=True)
    _print(output)
    lines = output.splitlines()
    pods = set([line.split()[0] for line in lines[1:]])
    success = set(
        # FIXME: we're ignoring delivery build right now as it will
        # need the atomic scan host for that.
        # ['build-1-build', 'delivery-1-build', 'test-1-build'])
        ['build-1-build', 'test-1-build', 'delivery-1-build']
    ).difference(pods)
    if success is False:
        raise Exception("Openshift builds did not persist after re provision.")
    _print("Openshift builds persited after re provision.")


def test_if_built_image_can_be_pulled(host, image, user='root', sudo=False):
    sudo = 'sudo' if sudo else ''
    cmd = (
        "{sudo} docker pull {image}"
    ).format(image=image, sudo=sudo)
    _cmd = (
        "ssh -t -o UserKnownHostsFile=/dev/null -o "
        "StrictHostKeyChecking=no {user}@{host} "
        "'{cmd}'"
    ).format(user=user, cmd=cmd, host=host)
    output = subprocess.check_output(_cmd, shell=True)
    _print(output)


def run():
    nodes = get_nodes(count=5)

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

    generate_ansible_inventory(jenkins_master_host,
                               jenkins_slave_host,
                               openshift_host,
                               scanner_host)

    run_cmd('iptables -F', host=openshift_host)
    run_cmd('iptables -F', host=jenkins_slave_host)

    setup_controller(controller)

    provision(controller)

    test_if_openshift_builds_are_complete(jenkins_slave_host)

    test_if_built_image_can_be_pulled(
        openshift_host,
        jenkins_slave_host + ':5000/bamachrn/python:release')

    provision(controller)

    test_if_openshift_builds_persist(jenkins_slave_host)

if __name__ == '__main__':
    run()
