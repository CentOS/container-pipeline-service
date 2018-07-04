"""
This file contains all function needed to maintain state accross validators.
"""
from os import path, mkdir, remove, getenv, environ, unsetenv
from uuid import uuid4

import ci.container_index.lib.utils as utils
from ci.container_index.lib.constants import StateKeys


class State(object):
    """
    Manages the state of needed by some validators
    """

    def __init__(self):
        self.state_location = str.format(
            "{}/.index_ci_{}",
            path.expanduser("~"),
            str(uuid4())
        )

        self.state_repos = path.join(self.state_location, "repos")
        self.state_file = path.join(self.state_location, "state")
        self.old_environ = dict(environ)
        unsetenv("GIT_ASKPASS")
        unsetenv("GIT_SSHPASS")

        if not path.exists(self.state_location):
            mkdir(self.state_location)
        if not path.exists(self.state_repos):
            mkdir(self.state_repos)

        self.data = None
        self.load()

    def clean_state(self):
        """
        Cleans up the state.
        """
        if path.exists(self.state_file):
            remove(self.state_file)
        environ.update(self.old_environ)

    def set_git_env(self):
        self.old_environ = dict(environ)
        environ["GIT_TERMINAL_PROMPT"] = "0"
        unsetenv("GIT_ASKPASS")
        unsetenv("GIT_SSHPASS")

    def unset_git_env(self):
        environ.update(self.old_environ)

    def git_update(self, git_url, git_branch):
        """
        Clones and checks out git repository specified git url and branch
        :param git_url: The url of repository to clone
        :param git_branch: The branch to checkout
        :return: The location of clone, if successful, else False
        """
        clone_location = path.join(
            self.state_repos,
            git_url.split(':')[-1].strip('//')
        )
        return utils.update_git_repo(
            git_url, git_branch,
            clone_location
        )

    def save(self):
        """
        Writes the state to external file
        """
        utils.dump_yaml(self.state_file, self.data)

    def load(self):
        """
        Loads the state from file
        :return:
        """
        if path.exists(self.state_file):
            self.data, err = utils.load_yaml(self.state_file)
            if err:
                raise Exception("Failed to read state file")
        else:
            self.data = {
                StateKeys.UNIQUE_IDS: {

                },
                StateKeys.UNIQUE_AJD: {

                }
            }
