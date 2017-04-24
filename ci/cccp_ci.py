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
    with open('env.properties') as f:
        s = f.read()

    _print('\n'.join(s.splitlines()[3:]))


if __name__ == '__main__':
    try:
        nodes = get_nodes(count=5)
        data = setup(nodes, options={
            'nfs_share': NFS_SHARE
        })
        test(data)
        teardown()
    except Exception as e:
        _print('Build failed: %s' % e)
        _print(run_cmd('cat /srv/pipeline-logs/cccp.log',
                       host=nodes[1]))
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
                pass
            with open('env.properties', 'a') as f:
                f.write('\nBUILD_FAILED=true\n')
        sys.exit(1)
