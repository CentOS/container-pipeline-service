import ci.container_index.lib.utils as utils
from os import path, mkdir, remove
from uuid import uuid4

STATE_LOCATION = str.format(
    "{}/.index_ci_{}",
    path.expanduser("~"),
    str(uuid4())
)
STATE_REPOS = path.join(STATE_LOCATION, "repos")
STATE_FILE = path.join(STATE_LOCATION, "state")


def init():
    if not path.exists(STATE_LOCATION):
        mkdir(STATE_LOCATION)
    if not path.exists(STATE_REPOS):
        mkdir(STATE_REPOS)


def clean_up():
    if path.exists(STATE_FILE):
        remove(STATE_FILE)


def git_update(git_url, git_branch):
    return utils.update_git_repo(
        git_url, git_branch,
        path.join(
            STATE_REPOS,
            git_url.split(':')[-1]
        )
    )


def dump_state(state):
    with open(STATE_FILE, "w+"):
        utils.dump_yaml(STATE_FILE, state)


def get_state():
    with open(STATE_FILE, "r"):
        data = utils.load_yaml(STATE_FILE)

    if not data or not isinstance(data, dict) or len(data) <= 0:
        data = {
            "Unique": None
        }

    return data
