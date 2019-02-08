"""
Contains all the constants used by index ci
"""


class FieldKeys(object):
    """
    Contains all the field keys that are present in the container index file
    or the cccp yaml file
    """
    PROJECTS = "Projects"
    ID = "id"
    APP_ID = "app-id"
    JOB_ID = "job-id"
    DESIRED_TAG = "desired-tag"
    GIT_URL = "git-url"
    GIT_PATH = "git-path"
    GIT_BRANCH = "git-branch"
    TARGET_FILE = "target-file"
    NOTIFY_EMAIL = "notify-email"
    BUILD_CONTEXT = "build-context"
    DEPENDS_ON = "depends-on"
    PREBUILD_SCRIPT = "prebuild-script"
    PREBUILD_CONTEXT = "prebuild-context"


class CheckKeys(object):
    """
    Contains extra data keys, used by some validators
    """
    CLONE = "clone"
    CLONE_LOCATION = "clone-location"
    STATE = "state"


class StateKeys(object):
    """
    Contains keys used to store data in state file.
    """
    UNIQUE_IDS = "Unique_IDS"
    UNIQUE_AJD = "Unique_AJD"


class RegexPatterns(object):
    """
    Contains regular expressions used by the validators
    """
    EMAIL = r"(\w+[.|\w])*@(\w+[.])*\w+"
