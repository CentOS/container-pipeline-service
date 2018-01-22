import json
import subprocess
import urllib2
from os import path, devnull
from shutil import rmtree

import yaml

FNULL = open(devnull, "w")


def print_msg(msg, verbose=False):
    if verbose:
        print(msg)


def load_yaml(yaml_path):
    """
    Load yaml data from specified file.
    :param yaml_path: The path of yaml file to load
    :return: The object repersenting the data f yaml file, None if load failed.
    """
    if not path.exists(yaml_path):
        raise Exception("The yaml file does not exist at " + yaml_path)
    with open(yaml_path, "r") as yaml_file:
        return yaml.load(yaml_file, Loader=yaml.BaseLoader)


def run_cmd(cmd, check_call=True, no_shell=False):
    """
    Run a specfied linux command
    :param cmd: The command to run
    :param check_call: If true, check call is used. Recommendedif no data is
    needed
    :param no_shell: If true, then command output is redirected to devnull
    """
    stdout = FNULL if no_shell else subprocess.PIPE
    if not check_call:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=stdout,
            stderr=subprocess.PIPE
        )
        process.communicate()
        if process.returncode > 0:
            raise Exception("Failed to execute command")
    else:
        subprocess.check_call(cmd)


def rm(p):
    """
    Removes the path from directoy structure, if it exists.
    :param p: The path to remove.
    """
    if path.exists(p):
        rmtree(p)


def request_url(url):
    """
    Queries a specified url and returns data, if any
    :param url: The url to query
    :return: The request object, or None upon failure.
    """
    try:
        req = urllib2.urlopen(url)
    except Exception:
        req = None

    return req


def clone_repo(git_url, clone_location):
    """
    Clones a git repo at specified location.
    :param git_url: The url of git repo
    :param clone_location: The path to clone repo.
    """
    cmd = ["git", "clone", git_url, clone_location]
    if path.exists(clone_location):
        rmtree(clone_location)
    run_cmd(cmd)


class RegistryInfo(object):
    """Stores/Caches metadata from specified registry"""

    def __init__(self, registry_url):
        """
        Initialize the info object
        :param registry_url: The URL of registry
        """
        self._registry_url = registry_url
        self.catalog = None
        self.tags = {}
        self.manifests = []
        self._load_info()

    def _load_info(self):
        """
        Loads the information about the registry to refer later.
        """
        # Get the catalog
        catalog_url = self._registry_url + "/_catalog"
        tags_info = "/tags/list"
        c = request_url(catalog_url)
        if c:
            self.catalog = json.load(c)["repositories"]
        else:
            raise Exception("Could not get registry catalog.")
        for item in self.catalog:
            tags_url = self._registry_url + "/" + item + tags_info
            tags_data = request_url(tags_url)
            if tags_data:
                self.tags[item] = json.load(tags_data)