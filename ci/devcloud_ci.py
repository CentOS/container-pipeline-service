#!/usr/bin/env python
import os
import sys
import getpass
import json

from ci.lib import setup, test, teardown, run_cmd, sync_controller

HELP_MESSAGE = """
Usage:
# Setup
devcloud_ci.py setup <jenkins_master_vm_id> \
<jenkins_slave_vm_id> \
<openshift_vm_id> \
<scanner_host_vm_id> \
<controller_vm_id>

# test
devcloud_ci.py test

# teardown
devcloud_ci.py teardown
"""

if __name__ == '__main__':
    sys.path.append(
        os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..')
        )
    )
    argc = len(sys.argv)
    if argc == 1 or argc > 1 and '-h' in sys.argv:
        print HELP_MESSAGE
        sys.exit(0)
    elif sys.argv[1] not in ('setup', 'test', 'teardown', 'sync'):
        print HELP_MESSAGE
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd == 'setup':
        cmd_str = 'onevm show %s | grep -i eth0_ip | cut -d "\\"" -f 2'
        user = getpass.getuser()
        nodes = [run_cmd(cmd_str % vmid, user=user).strip()
                 for vmid in sys.argv[2:7]]
        data = setup(nodes, options={
            'nfs_share': '/nfsshare'
        })
        with open('test.json', 'w') as f:
            f.write(json.dumps(data))
    elif cmd == 'test':
        test_path = ' '.join(sys.argv[2:]) if argc > 2 else ''
        with open('test.json') as f:
            data = json.load(f)
        test(data, test_path)
    elif cmd == 'teardown':
        teardown()
    elif cmd == 'sync':
        with open('test.json') as f:
            data = json.load(f)
            controller = data['hosts']['controller']['host']
        sync_controller(controller, stream=True)
