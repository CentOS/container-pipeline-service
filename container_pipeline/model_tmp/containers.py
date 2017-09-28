import subprocess

#from django.db import models
#from django.conf import settings
from os import path
from json import load, dump


def form_dockerfile_link(git_url, git_path, git_branch, target_file):
    link_url = None
    if "github" in git_url or "gitlab" in git_url:
        link_url = str.format(
            "{git_url}/blob/{git_branch}/{git_path}/{target_file}",
            git_url=git_url,
            git_branch=git_branch,
            git_path=git_path,
            target_file=target_file
        )
    return link_url


class ContainerModel(object):

    def __init__(self, data_dir="/srv/pipeline-logs"):
        self._data_dir = data_dir
        self.data_file = data_dir + "/container_info.json"
        self.data = {
        }
        if path.exists(self.data_file):
            self.read()
        else:
            self.write()

    def read(self):
        with open(self.data_file, "r") as f:
            self.data = load(f)

    def write(self):
        with open(self.data_file, "w+") as f:
            dump(self.data, f)

    def append_info(self, container_name, dockerfile_link):
        if container_name not in self.data:
            self.data[container_name] = {
                "name": container_name,
                "dockerfile_link": ""
            }
        self.data[container_name]["dockerfile_link"] = dockerfile_link

    def delete_info(self, container_name):
        if container_name in self.data:
            self.data.pop(container_name, None)