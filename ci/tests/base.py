import os
import copy
import json
import time
import unittest
from xml.dom.minidom import parseString

from ci.lib import provision, run_cmd, _print


class BaseTestCase(unittest.TestCase):
    """Base test case to extend test cases from"""

    def setUp(self):
        self.hosts = json.loads(os.environ.get('CCCP_CI_HOSTS') or "{}") or {
            'openshift': {
                'host': '192.168.100.200',
                'private_key': '~/.vagrant.d/insecure_private_key',
                'remote_user': 'vagrant'
            },
            'jenkins_master': {
                'host': '192.168.100.100',
                'private_key': '~/.vagrant.d/insecure_private_key',
                'remote_user': 'vagrant'
            },
            'jenkins_slave': {
                'host': '192.168.100.100',
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

    def provision(self, force=False, extra_args=""):
        """
        Provision CCCP nodes.

        By default, it runs provisioning only for the first time, and
        skips for the subsequent calls.

        Args:
            force (bool): Provision forcefully.
            extra_args (str): Extra cmd line args for running ansible playbook
        """
        controller = copy.copy(self.hosts['controller'])
        controller['hosts'] = None
        _print('Provisioning...')
        provisioned, out = provision(
            controller, force=force, extra_args=extra_args)
        if provisioned:
            _print(out[-1000:])

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

    def cleanup_openshift(self):
        try:
            print self.run_cmd(
                'oc --config /var/lib/origin/openshift.local.config/master/'
                'admin.kubeconfig delete project '
                '53b1a8ddd3df5d4fd94756e8c20ae160e565a4b339bfb47165285955',
                host=self.hosts['openshift']['host'])
        except:
            pass
        time.sleep(10)

    def cleanup_beanstalkd(self):
        print self.run_cmd('systemctl stop cccp_imagescanner',
                           host=self.hosts['jenkins_master']['host'])
        print self.run_cmd('systemctl stop cccp-dockerfile-lint-worker',
                           host=self.hosts['jenkins_slave']['host'])
        print self.run_cmd('systemctl stop cccp-scan-worker',
                           host=self.hosts['scanner']['host'])
        print self.run_cmd('docker stop build-worker; '
                           'docker stop delivery-worker; '
                           'docker stop dispatcher-worker',
                           host=self.hosts['jenkins_slave']['host'])

        print self.run_cmd('systemctl restart beanstalkd',
                           host=self.hosts['openshift']['host'])
        time.sleep(5)

        print self.run_cmd('docker start build-worker; '
                           'docker start delivery-worker; '
                           'docker start dispatcher-worker',
                           host=self.hosts['jenkins_slave']['host'])
        print self.run_cmd('systemctl start cccp-dockerfile-lint-worker',
                           host=self.hosts['jenkins_slave']['host'])
        print self.run_cmd('systemctl start cccp-scan-worker',
                           host=self.hosts['scanner']['host'])
        print self.run_cmd('systemctl start cccp_imagescanner',
                           host=self.hosts['jenkins_master']['host'])

    def get_jenkins_builds_for_job(self, job):
        """Get builds for a Jenkins job"""
        s = self.run_cmd('curl -g "http://localhost:8080/job/%s/api/xml?'
                         'tree=allBuilds[result,number]&"' % job,
                         host=self.hosts['jenkins_master']['host']).strip()
        dom = parseString(s)
        builds = [child.getElementsByTagName('number')[0].childNodes[0].data
                  for child in dom.childNodes[0].childNodes]
        return builds
