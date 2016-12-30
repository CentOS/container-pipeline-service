import subprocess
import os
import sys

url_base = os.environ.get('URL_BASE')
api = os.environ.get('API')
ver = "7"
arch = "x86_64"
count = 4


def _print(msg):
    print msg
    sys.stdout.flush()


def run_cmd(cmd, user='root', host=None, private_key='', stream=False):
    if host:
        private_key_args = ''
        if private_key:
            private_key_args = '-i {path}'.format(
                path=os.path.expanduser(private_key))
        _cmd = (
            "ssh -t -o UserKnownHostsFile=/dev/null -o "
            "StrictHostKeyChecking=no {private_key_args} {user}@{host} '"
            "{cmd}"
            "'"
        ).format(user=user, cmd=cmd, host=host,
                 private_key_args=private_key_args)
    else:
        _cmd = cmd

    p = subprocess.Popen(_cmd, shell=True,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    if stream:
        out = ""
        for line in iter(p.stdout.readline, ''):
            _print(line.strip())
            out += line
        err = p.stderr.read()
    else:
        out, err = p.communicate()
    _print("=" * 30 + "ERROR" + "=" * 30)
    _print([err, p.returncode])
    if p.returncode is not None and p.returncode != 0:
        raise Exception(err)
    return out


class ProvisionHandler(object):

    def __init__(self):
        self._provisioned = True if os.environ.get(
            'CCCP_CI_PROVISIONED', None) == 'true' else False

    def run(self, controller, force=False):
        if not force and self._provisioned:
            return

        host = controller.get('host')

        workdir = os.path.expanduser(controller.get('workdir') or '') or \
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)), '../')
        private_key = os.path.expanduser(
            controller.get('private_key') or '') if not host else \
            controller.get('private_key')

        private_key_args = (
            '--private-key=%s' % private_key if private_key else '')

        inventory = os.path.join(workdir, controller.get('inventory_path'))
        user = controller.get('user', 'root')
        cmd = (
            "cd {workdir} && "
            "ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i {inventory} "
            "-u {user} -s {private_key_args} provisions/vagrant.yml"
        ).format(workdir=workdir, inventory=inventory, user=user,
                 private_key_args=private_key_args)
        _print('Provisioning command: %s' % cmd)
        run_cmd(cmd, host=host, stream=True)
        self._provisioned = True

provision = ProvisionHandler().run
