"""
This file contains all function needed to maintain state accross validators.
"""
from os import path, mkdir, remove
from uuid import uuid4

import ci.container_index.lib.utils as utils
from ci.container_index.lib.constants import StateKeys

# STATE_LOCATION = Location where state information is stored
STATE_LOCATION = str.format(
    "{}/.index_ci_{}",
    path.expanduser("~"),
    str(uuid4())
)
# Location where git repos are cloned.
STATE_REPOS = path.join(STATE_LOCATION, "repos")
# Location of state file wherer state is dumped
STATE_FILE = path.join(STATE_LOCATION, "state")


def init():
    """
    Initialize the state, creating necessary directories, if they don't exist
    """
    if not path.exists(STATE_LOCATION):
        mkdir(STATE_LOCATION)
    if not path.exists(STATE_REPOS):
        mkdir(STATE_REPOS)


def clean_up():
    """
    Removes the state tracking file.
    """
    if path.exists(STATE_FILE):
        remove(STATE_FILE)


def git_update(git_url, git_branch):
    """
    Clones provided git repository and checks out specified git branch in
    STATE_REPOS.
    :param git_url: The URL of the git repository to clone
    :param git_branch: The branch to check out in the git repository
    :return The location where the clone happened.
    """
    clone_location = path.join(
        STATE_REPOS,
        git_url.split(':')[-1].strip('//')
    )
    return utils.update_git_repo(
        git_url, git_branch,
        clone_location
    )


def dump_state(state):
    """
    Dumps current state into state file
    :param state: The state information to dump
    :return:
    """
    utils.dump_yaml(STATE_FILE, state)


def get_state():
    """
    Gets the state as stored in state file or initializes state.
    :return: Current state, either from file or initialized.
    """
    data = None
    if path.exists(STATE_FILE):
        with open(STATE_FILE, "r"):
            data = utils.load_yaml(STATE_FILE)

    if not data or not isinstance(data, dict) or len(data) <= 0:
        data = {
            StateKeys.UNIQUE_IDS: {

            },
            StateKeys.UNIQUE_AJD: {

            }
        }

    return data
