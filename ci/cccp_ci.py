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
import os
import urllib

from .lib import _print, generate_ansible_inventory, run_cmd, provision

url_base = os.environ.get('URL_BASE')
api = os.environ.get('API')
ver = "7"
arch = "x86_64"
count = 4

repo_url = os.environ.get('ghprbAuthorRepoGitUrl') or \
    os.environ.get('GIT_URL')
repo_branch = os.environ.get('ghprbSourceBranch') or \
    os.environ.get('ghprbTargetBranch') or 'master'


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


    test_if_built_image_can_be_pulled(
        openshift_host,
        jenkins_slave_host + ':5000/bamachrn/python:release')

    provision(controller)

    test_if_openshift_builds_persist(jenkins_slave_host)

if __name__ == '__main__':
    try:
        run()
    except Exception as e:
        _print('Build failed: %s' % e)
        _print('Reserving nodes for debugging...')
        fail_nodes()
        _print('=' * 10 + 'Node Info' + '=' * 10)
        print_nodes()
        sys.exit(1)
