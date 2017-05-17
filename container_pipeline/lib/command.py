# -*- coding: utf-8 -*-
import subprocess


def run_cmd(cmd, shell=False):
    """
    Runs a shell command.

    :param cmd: Command to run
    :param shell: Whether to run raw shell commands with '|' and redirections
    :type cmd: str
    :type shell: boolean

    :return: Command output
    :rtype: str
    :raises: subprocess.CalledProcessError
    """
    if shell:
        subprocess.check_output(cmd, shell=True)
    else:
        subprocess.check_output(cmd.split(), shell=False)
