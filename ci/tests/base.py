import os
import json
import unittest

from ci.lib import provision, run_cmd


class BaseTestCase(unittest.TestCase):
    """Base test case to extend test cases from"""

    def setUp(self):
        self.hosts = json.loads(os.environ.get('CCCP_CI_HOSTS') or "{}") or {
            'openshift': {
                'host': '192.168.100.201',
                'private_key': '~/.vagrant.d/insecure_private_key',
                'remote_user': 'vagrant'
            },
            'jenkins_master': {
                'host': '192.168.100.100',
                'private_key': '~/.vagrant.d/insecure_private_key',
                'remote_user': 'vagrant'
            },
            'jenkins_slave': {
                'host': '192.168.100.200',
                'private_key': '~/.vagrant.d/insecure_private_key',
                'remote_user': 'vagrant'
            },
            'controller': {
                'host': None,
                'private_key': '~/.vagrant.d/insecure_private_key',
                'user': 'vagrant',
                # 'workdir': 'path/to/project/'
                # relative to this source dir
                'inventory_path': 'provisions/hosts.vagrant'
            }
        }

    def provision(self, force=False):
        """
        Provision CCCP nodes.

        By default, it runs provisioning only for the first time, and
        skips for the subsequent calls.

        Args:
            force (bool): Provision forcefully.
        """
        provision(self.hosts['controller'], force=force)

    def run_cmd(self, cmd, user=None, host=None, stream=False):
        """
        Run command on local or remote machine (over SSH).

        Args:
            cmd (str): Command to execute
            user (str): Remote user to execute command as
            host (str): Remote host
            stream (bool): Whether to stream output or not

        Returns:
            Output string

        Raises:
            Exception if command execution fails
        """
        host_info = self.hosts.get(self.node)
        return run_cmd(cmd, user=user or host_info['remote_user'],
                       host=host or host_info['host'],
                       private_key=host_info.get('private_key'),
                       stream=stream)
