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
import sys
from time import sleep

from ci.lib import _print, setup, test, teardown, \
    run_cmd, DEPLOY_LOGS_PATH, run_cccp_index_job, run_pep8_gate


DEBUG = os.environ.get('ghprbCommentBody', None) == '#dotests-debug'
ver = "7"
arch = "x86_64"
count = 4
NFS_SHARE = "/nfsshare"
# number of retries if failed receiving nodes from CICO
CICO_GET_RETRY_COUNT = 3
# number of seconds to helo VMs if #dotests-debug is commented on PR
DEBUG_SECONDS = 7200

# repo_url = os.environ.get('ghprbAuthorRepoGitUrl') or \
#     os.environ.get('GIT_URL')
# repo_branch = os.environ.get('ghprbSourceBranch') or \
#     os.environ.get('ghprbTargetBranch') or 'master'


def get_nodes(ver="7", arch="x86_64", count=4):
    """ Utility function to get nodes from CICO infrastructure.

    Request given count of CentOS of particular version and architecture.
    CICO returns JSON, with hostnames of nodes provisioned.
    duffy.key is need for requesting nodes.

    Args:
        ver (str):
            Version of CentOS to be installed on node
            viz ["6", "7"]. Defaults to "7".
        arch (str): Architecture of CentOS to be install on node.
            Defaults to "x86_64".
        count (int): Number of CentOS nodes to be requested. Defaults to 4.

    Returns:
        List of hostnames received from CICO.

    Note:
        This function also appends DUFFY_SSID to a local file
        env.properties .
        Also prints the output received from CICO.
    """
    out = run_cmd(
        'export CICO_API_KEY=`cat ~/duffy.key` && '
        'cico node get --arch %s --release %s --count %s '
        '--format json' % (arch, ver, count))
    _print('Get nodes output: %s' % out)
    hosts = json.loads(out)

    with open('env.properties', 'a') as f:
        f.write('DUFFY_SSID=%s' % hosts[0]['comment'])
        f.close()

    return [host['hostname'] for host in hosts]


def print_nodes():
    """
    Function to print nodes from a local file env.properties.
    """
    with open('env.properties') as f:
        s = f.read()

    _print('\n'.join(s.splitlines()[3:]))


def _if_debug():
    """
    If whitelisted github user has added "dotests-debug" string as comment
    on a given PR, the nodes are kept for 2 hours for debugging, once
    time lapses the nodes are returned to CICO infrastructure.
    """
    if DEBUG:
        _print('Reserving nodes for debugging...')
        _print('=' * 10 + 'Node Info' + '=' * 10)
        print_nodes()
        try:
            _print('Sleeping for %s seconds for debugging...'
                   % str(DEBUG_SECONDS))
            sleep(DEBUG_SECONDS)
        except Exception as e:
            _print(e)
        with open('env.properties', 'a') as f:
            f.write('\nBUILD_FAILED=true\n')


if __name__ == '__main__':
    try:
        # get nodes from CICO infra
        while CICO_GET_RETRY_COUNT > 0:
            try:
                nodes = get_nodes(count=5)
            except Exception as e:
                _print("Failed to get nodes from CICO. Error %s" % str(e))
                CICO_GET_RETRY_COUNT -= 1
                _print("Retrying get nodes from CICO, count=%d" %
                       CICO_GET_RETRY_COUNT)
                # sleep for one minute
                sleep(int(60))
            else:
                _print(str(nodes))
                break
        if CICO_GET_RETRY_COUNT == 0:
            _print('Build failed while receiving nodes from CICO:\n%s' % e)
            # _if_debug is not needed, since we dont have even nodes to debug
            sys.exit(1)
    except Exception as e:
        _print('Build failed while receiving nodes from CICO:\n%s' % e)
        # _if_debug is not needed, since we dont have even nodes to debug
        sys.exit(1)

    # run pep8 checks on controller node before running actual tests
    try:
        # run the pep8 checks on source code
        run_pep8_gate(nodes[4])
    except Exception as e:
        _print('Build failed as pep8 checks failed tests failed.')
        _if_debug()
        sys.exit(1)

    try:
        # deploy service on given set of nodes
        # TODO: export deployment logs in a file
        data = setup(nodes, options={
            'nfs_share': NFS_SHARE
        })
    except Exception as e:
        _print('Build failed during deployment:\n%s' % e)
        _if_debug()
        # first cat the deployment logs, nodes[4]=controller node
        _print(run_cmd('cat %s' % DEPLOY_LOGS_PATH, host=nodes[4]))
        sys.exit(1)

    try:
        # run cccp-index job and run test CI projects, nodes[0]=jenkins_master
        run_cccp_index_job(jenkins_master=nodes[0])
    except Exception as e:
        _print("Error running cccp-index job and test builds:\n%s" % e)
        _if_debug()
        # then cat the cccp.log, nodes[1]=jenkins slave
        _print(run_cmd('cat /srv/pipeline-logs/cccp.log', host=nodes[1]))
        sys.exit(1)

    try:
        # run the given tests
        _print("Running the tests..")
        test(data)
    except Exception as e:
        _print('Build failed as tests failed: %s' % e)
        _if_debug()
        sys.exit(1)

    # tear down after running tests
    teardown()
