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


def get_nodes(ver="7", arch="x86_64", count=4):
    get_nodes_url = "%s/Node/get?key=%s&ver=%s&arch=%s&count=%s" % (
        url_base, api, ver, arch, count)

    resp = urllib.urlopen(get_nodes_url).read()
    data = json.loads(resp)
    with open('env.properties', 'a') as f:
        f.write('DUFFY_SSID=%s' % data['ssid'])
        f.close()
    sys.stdout.write(resp)
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
                               openshift_host):

    ansible_inventory = ("""
[all:children]
jenkins_master
jenkins_slaves
openshift

[jenkins_master]
{jenkins_master_host}

[jenkins_slaves]
{jenkins_slave_host}

[openshift]
{openshift_host}

[all:vars]
public_registry= {jenkins_slave_host}
jenkins_private_key_file = jenkins.key
jenkins_public_key_file = jenkins.key.pub
cccp_index_repo=https://github.com/bamachrn/cccp-index.git
copy_ssl_certs=true
openshift_startup_delay=150

[jenkins_master:vars]
oc_slave={jenkins_slave_host}""").format(
        jenkins_master_host=jenkins_master_host,
        jenkins_slave_host=jenkins_slave_host,
        openshift_host=openshift_host)

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
        "yum install -y ansible1.9 python2-jenkins-job-builder",
        host=controller)

    run_cmd(
        "scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -r "
        "./ root@%s:/root/centos-cccp-ansible" % controller)


def provision(controller):
    run_cmd(
        "cd /root/centos-cccp-ansible && "
        "ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i hosts -u root "
        "--private-key=/root/.ssh/id_rsa vagrant.yml",
        host=controller)


def test_if_openshift_builds_are_running(host):
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
    while retries < 100 and success is False:
        if retries > 0:
            time.sleep(60)
        sys.stdout.write("Retries: %d/100" % retries)
        try:
            output = subprocess.check_output(_cmd, shell=True)
            sys.stdout.write(output)
            lines = output.splitlines()
            pods = set([line.split()[0] for line in lines[1:]])
            success = pods == set(
                ['build-1-build', 'delivery-1-build', 'test-1-build'])
        except subprocess.CalledProcessError:
            success = False
        retries += 1
    if success is False:
        raise Exception("Openshift builds not running.")
    sys.stdout.write("Openshift builds running successfully.")


def test_if_openshift_builds_persist(host):
    sys.stdout.write("=" * 30)
    sys.stdout.write("Test if openshift builds persist after reprovision")
    sys.stdout.write("=" * 30)
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
    sys.stdout.write(output)
    lines = output.splitlines()
    pods = set([line.split()[0] for line in lines[1:]])
    success = pods == set(
        ['build-1-build', 'delivery-1-build', 'test-1-build'])
    if success is False:
        raise Exception("Openshift builds did not persist after re provision.")
    sys.stdout.write("Openshift builds persited after re provision.")


def run():
    nodes = get_nodes()

    jenkins_master_host = nodes[0]
    jenkins_slave_host = nodes[1]
    openshift_host = nodes[2]
    controller = nodes.pop()

    nodes_env = (
        "\nJENKINS_MASTER_HOST=%s\n"
        "JENKINS_SLAVE_HOST=%s\n"
        "OPENSHIFT_HOST=%s\n"
        "CONTROLLER=%s\n"
    ) % (jenkins_master_host, jenkins_slave_host,
         openshift_host, controller)

    with open('env.properties', 'a') as f:
        f.write(nodes_env)

    generate_ansible_inventory(jenkins_master_host,
                               jenkins_slave_host,
                               openshift_host)

    run_cmd('iptables -F', host=openshift_host)

    setup_controller(controller)

    provision(controller)

    test_if_openshift_builds_are_running(jenkins_slave_host)

    provision(controller)

    test_if_openshift_builds_persist(jenkins_slave_host)

if __name__ == '__main__':
    run()
