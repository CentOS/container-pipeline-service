# lib.py containing library functions

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
        return subprocess.check_output(cmd, shell=True)
    else:
        return subprocess.check_output(cmd.split(), shell=False)


def run_cmd_out_err(cmd):
    """
    Runs a shell command and returns output & error (if any)

    :param cmd: Command to run
    :type cmd: tuple or list

    :return: Command output
    :rtype: str, int
    """
    return subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE).communicate()
