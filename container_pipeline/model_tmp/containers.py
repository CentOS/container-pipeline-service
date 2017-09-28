import subprocess

#from django.db import models
#from django.conf import settings
from os import path
from json import load, dump

# TODO : Change implementation into proper model and move this class into model package.


def form_dockerfile_link(git_url, git_path, git_branch, target_file):
    """
    Helper function to generate docker file link.
    :param git_url: The url of the git repository.
    :param git_path: The path, relative to the git repository root, where the file resides.
    :param git_branch: The repository branch where the file resides.
    :param target_file: The name of the target file.
    :return: The reachable link to the dockerfile.
    """

    # TODO : Move this into a lib.

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


class ContainerLinksModel(object):
    """Represents information about the container, stored in the model."""

    def __init__(self, data_dir="/srv/pipeline-logs"):
        """
        Intialize the Model
        :param data_dir: The directory to which we need to dump the data file to.
        """
        self._data_dir = data_dir
        self.data_file = data_dir + "/container_info.json"
        self.data = {
        }
        if path.exists(self.data_file):
            self.unmarshall()
        else:
            self.marshall()

    def unmarshall(self):
        """Loads the modal information into the object."""

        with open(self.data_file, "r") as f:
            self.data = load(f)

    def marshall(self):
        """Saves the model information"""

        with open(self.data_file, "w+") as f:
            dump(self.data, f)

    def append_info(self, container_name, dockerfile_link):
        """
        Appends the container information to the model
        :param container_name: The name of the container
        :param dockerfile_link: The link to the dockerfile.
        """
        if container_name not in self.data:
            self.data[container_name] = {
                "name": container_name,
                "dockerfile_link": ""
            }
        self.data[container_name]["dockerfile_link"] = dockerfile_link

    def delete_info(self, container_name):
        """
        Given a container name, deletes information about it, if it exists.
        :param container_name: The name of the container.
        """
        if container_name in self.data:
            self.data.pop(container_name, None)