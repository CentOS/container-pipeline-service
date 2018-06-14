import yaml

from datetime import datetime, date

from glob import glob
from os import environ, path, mkdir, unsetenv, listdir,\
    unlink, devnull, getenv, getcwd, chdir, system, remove
from shutil import rmtree

from subprocess import check_call, CalledProcessError, STDOUT


def execute_command(cmd):
    """Execute a specified command"""
    try:
        fnull = open(devnull, "w")
        check_call(cmd, stdout=fnull, stderr=STDOUT)
    except CalledProcessError:
        return False
    return True


def load_yaml(file_path):
    data = None
    err = None
    try:
        with open(file_path, "r") as f:
            data = yaml.load(f)
    except Exception as e:
        err = e.message
    return data, err


def dump_yaml(file_path, data):
    err = None
    try:
        with open(file_path, "w") as f:
            yaml.dump(f)
    except Exception as e:
        err = e.message
    return err


def update_git_repo(git_url, git_branch, clone_location="."):
    ret = None

    if not path.exists(clone_location):
        clone_command = ["git", "clone", git_url, clone_location]
        if not execute_command(clone_command):
            return None

    get_back = getcwd()
    chdir(clone_location)

    # This command fetches all branches of added remotes of git repo.
    branches_cmd = r"""git branch -r | grep -v '\->' | while
    read remote; do git branch --track "${remote#origin/}"
    $remote" &> /dev/null; done"""

    system(branches_cmd)
    cmd = ["git", "fetch", "--all"]
    execute_command(cmd)

    # Pull for update
    cmd = ["git", "pull", "--all"]
    execute_command(cmd)

    # Checkout required branch
    cmd = ["git", "checkout", "origin/" + git_branch]

    if execute_command(cmd):
        ret = clone_location
    chdir(get_back)
    return ret


def print_out(data, verbose=True):
    if verbose:
        print(data)


class IndexCIMessage(object):

    def __init__(self, data, title=None):
        self.title = title if title else "Untitled"
        self.success = True
        self.data = data
        self.errors = []
        self.warnings = []
