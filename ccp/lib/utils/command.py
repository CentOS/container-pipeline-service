# -*- coding: utf-8 -*-
from ccp.lib.exceptions import CommandOutputError
import subprocess


def run_command(cmd, shell=False, use_pipes=True):
    """
    Runs a shell command
    :param cmd: The command that needs to be run.
    :type cmd: s
    :param shell: Default False: Whether to run raw shell commands with '|' and
    redirections
    :param use_pipes: Default False: If true, then pipes are used for
    communication
    :return: Command output and err
    :raises subprocess.CalledProcessError
    """
    p = subprocess.Popen(
        cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) if use_pipes else subprocess.Popen(
        cmd, shell=shell
    )
    out, err = p.communicate()
    return out, err


def run_command_exception_on_stderr(cmd, shell=False, use_pipes=True):
    """
    Runs a shell command, raised exception if stderr
    :param cmd: The command that needs to be run.
    :param shell: Default False: Whether to run raw shell commands with '|' and
    redirections
    :param use_pipes: Default True: If true, then pipes are used for
    communication
    :return: Command output and err
    :raises subprocess.CalledProcessError
    :raises ccp.lib.exceptions.CommandOutputError
    """
    out, err = run_command(cmd, shell=shell, use_pipes=use_pipes)
    if err:
        raise CommandOutputError(err)
    return out
