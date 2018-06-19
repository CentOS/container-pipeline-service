
class FieldKeys(object):
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

class StateKeys(object):
    UNIQUE_IDS = "Unique_IDS"
    UNIQUE_AJD = "Unique_AJD"


class RegexPatterns(object):
    EMAIL = r"(\w+[.|\w])*@(\w+[.])*\w+"
