import subprocess

from django.db import models
from django.conf import settings
from os import path
from yaml import load


def form_dockerfile_link(git_url, git_path, target_file):
    pass


class ContainerInfo(object):

    def __init__(self, data_dir="/srv/pipeline-logs"):
        self._data_dir = data_dir
        self.data_file = data_dir + "/container_info.yaml"
        self.data = {

        }

    def append_info(self, container_name, dockerfile_link):
        if container_name not in self._data_dir:
            self.data[container_name] = {
                "name": container_name,
                "dockerfile_link": ""
            }

        self.data[container_name]["dockerfile_link"] = dockerfile_link