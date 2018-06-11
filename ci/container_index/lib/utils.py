import yaml
from datetime import datetime, date
from glob import glob
from os import environ, path, mkdir, unsetenv, listdir,\
    unlink, devnull, getenv, getcwd, chdir, system
from shutil import rmtree
from subprocess import check_call, CalledProcessError, STDOUT

def execute_command(cmd):
    """Execute a specified command"""
    try:
        fnull = open(devnull, "w")
        check_call(cmd, stdout=fnull, stderr=STDOUT)
        return True
    except CalledProcessError:
        return False

def load_yaml(file_path):
    data = None
    try:
        with open(file_path, "r") as f:
            data = yaml.load(f)
    except Exception as e:
        pass
    return data

def dump_yaml(file_path, data):
    try:
        with open(file_path, "w") as f:
            yaml.dump(f)
    except Exception as e:
        pass

def update_git_repo(git_url, git_branch, clone_location="."):
    t = git_url.split(':')[1] if ':' in git_url else git_url
    clone_path = path.join(clone_location, t)
    ret = None
    
    if not path.exists(clone_path):
        clone_command = ["git", "clone", git_url, clone_path]
        if not execute_command(clone_command):
            return None
    
    get_back = getcwd()
    chdir(clone_path)

    branches_cmd = "git branch -r | grep -v '\->' | while read remote; do git branch --track \"${remote#origin/}\"" \
          " \"$remote\" &> /dev/null; done"

    system(branches_cmd)
    cmd = ["git", "fetch", "--all"]
    execute_command(cmd)

    # Pull for update
    cmd = ["git", "pull", "--all"]
    execute_command(cmd)

    # Checkout required branch
    cmd = ["git", "checkout", "origin/" + git_branch]

    if execute_command(cmd):
        ret = clone_path
    return ret

class IndexCIMessage(object):

    def __init__(self, data, title=None):
        self.title = title if title else "Untitled"
        self.success = True
        self.data = data
        self.errors = []
        self.warnings = []