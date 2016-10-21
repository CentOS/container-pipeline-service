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
    try:
        run()
    except Exception as e:
        _print('Build failed: %s' % e)
        _print('Reserving nodes for debugging...')
        fail_nodes()
        _print('=' * 10 + 'Node Info' + '=' * 10)
        print_nodes()
        sys.exit(1)
