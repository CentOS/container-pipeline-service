# -*- coding: utf-8 -*-
from ccp.lib.exceptions import CommandOutputError
import subprocess


def run_command(cmd, shell=False):
    """
    Runs a shell command
    :param cmd: The command that needs to be run.
    :type cmd: s
    :param shell: Default False: Whether to run raw shell commands with '|' and
    redirections
    :return: Command output and err
    :raises subprocess.CalledProcessError
    """
    p = subprocess.Popen(cmd, shell=shell)
    out, err = p.communicate()
    return out, err


def run_command_exception_on_stderr(cmd, shell=False):
    """
    Runs a shell command, raised exception if stderr
    :param cmd: The command that needs to be run.
    :param shell: Default False: Whether to run raw shell commands with '|' and
    redirections
    :return: Command output and err
    :raises subprocess.CalledProcessError
    :raises ccp.lib.exceptions.CommandOutputError
    """
    out, err = run_command(cmd, shell=shell)
    if err:
        raise CommandOutputError(err)
    return out
