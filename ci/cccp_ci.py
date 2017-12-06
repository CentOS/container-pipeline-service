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

from ci.lib import _print, setup, test, teardown, run_cmd

DEBUG = os.environ.get('ghprbCommentBody', None) == '#dotests-debug'
ver = "7"
arch = "x86_64"
count = 4
NFS_SHARE = "/nfsshare"


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
                   % 7200)
            import time
            time.sleep(int(7200))
        except Exception as e:
            _print(e)
        with open('env.properties', 'a') as f:
            f.write('\nBUILD_FAILED=true\n')
    sys.exit(1)


if __name__ == '__main__':
    try:
        # get nodes from CICO infra
        nodes = get_nodes(count=5)
    except Exception as e:
        _print('Build failed while receiving nodes from CICO: %s' % e)
        _if_debug()
        sys.exit(1)

    try:
        # deploy service on given set of nodes
        # TODO: export deployment logs in a file
        data = setup(nodes, options={
            'nfs_share': NFS_SHARE
        })
    except Exception as e:
        _print('Build failed in either deployment or running builds: %s' % e)
        # TODO: cat deployment logs
        _if_debug()
        _print(run_cmd('cat /srv/pipeline-logs/cccp.log',
                       host=nodes[1]))
        sys.exit(1)

    try:
        # run the given tests
        test(data)
    except Exception as e:
        _print('Build failed as tests failed: %s' % e)
        sys.exit(1)

    # tear down after running tests
    teardown()
