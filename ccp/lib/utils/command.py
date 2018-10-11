# -*- coding: utf-8 -*-
from ccp.lib.exceptions import CommandOutputError
import subprocess


def run_command(cmd, shell=False):
    """
    Runs a shell command
    :param cmd: The command that needs to be run.
    :param shell: Default False: Whether to run raw shell commands with '|' and
    redirections
    :return: Command output
    :raises subprocess.CalledProcessError
    :raises ccp.lib.exceptions.CommandOutputError
    """
    p = subprocess.Popen(cmd, shell=shell)
    out, err = p.communicate()
    if err:
        raise CommandOutputError(err)
    return out
