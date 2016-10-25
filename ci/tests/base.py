import os
import json
import unittest

from ci.lib import provision, run_cmd


class BaseTestCase(unittest.TestCase):

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
        provision(self.hosts['controller'], force=force)

    def run_cmd(self, cmd, user=None, host=None, stream=False):
        host_info = self.hosts.get(self.node)
        return run_cmd(cmd, user=user or host_info['remote_user'],
                       host=host or host_info['host'],
                       private_key=host_info['private_key'],
                       stream=stream)
