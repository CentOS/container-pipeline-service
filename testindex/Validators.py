from NutsAndBolts import GlobalEnvironment, execute_command
from os import path, getcwd, chdir, system
from yaml import load
from Summary import Summary


class Validator:
    """Top level class for validators"""

    def __init__(self, index_file=None):
        self._file_name = path.basename(index_file)

        self._index_file = index_file
        self._success = True
        self._load_yaml()

    def _load_yaml(self):

        with open(self._index_file, "r") as ymlfile:
            self._yaml = load(ymlfile)["Projects"]

    def run(self):
        """Runs the Validator, returning True or False based on success or failure"""
        raise NotImplementedError("Implement this method.")


class IndexFormatValidator(Validator):
    """Checks the format of index files"""

    def __init__(self, index_file):

        Validator.__init__(self, index_file)

    def run(self):

        id_list = []

        for entry in self._yaml:

            summary_collector = Summary.get_summary_collector(self._file_name, entry)

            # Check if id field exists
            if "id" not in entry or ("id" in entry and entry["id"] is None):
                self._success = False
                summary_collector["errors"].append("Missing id")

            else:
                # Check if id has not already been passed
                if entry["id"] in id_list:
                    self._success = False
                    summary_collector["errors"].append("id field must be unique in the file")

                else:
                    id_list.append(entry["id"])

            # Checking app-id field
            if "app-id" not in entry or ("app-id" in entry and entry["app-id"] is None):
                self._success = False
                summary_collector["errors"].append("Missing app-id")

            else:
                if entry["app-id"] != self._file_name.split(".")[0]:
                    self._success = False
                    summary_collector["errors"].append("app-id should be same as first part of the file name")

                if "_" in entry["app-id"] or "/" in entry["app-id"] or "." in entry["app-id"]:
                    self._success = False
                    summary_collector["errors"].append("app-id cannot contain _, / or . character.")

            # Checking job-id field
            if "job-id" not in entry or ("job-id" in entry and entry["job-id"] is None):
                self._success = False
                summary_collector["errors"].append("Missing job-id field")

            else:
                if "_" in entry["job-id"] or "/" in entry["job-id"] or "." in entry["job-id"]:
                    self._success = False
                    summary_collector["errors"].append("job-id cannot contain _, / or . character.")

            # Check for git-url
            if "git-url" not in entry or ("git-url" in entry and entry["git-url"] is None):
                self._success = False
                summary_collector["errors"].append("Missing git-url")

            # Checking git-path
            if "git-path" not in entry or ("git-path" in entry and entry["git-path"] is None):
                self._success = False
                summary_collector["errors"].append("Missing git-path")

            # Check git-branch
            if "git-branch" not in entry or ("git-branch" in entry and entry["git-branch"] is None):
                self._success = False
                summary_collector["errors"].append("Missing git-branch")

            # Check target-file
            if "target-file" not in entry or ("target-file" in entry and entry["target-file"] is None):
                self._success = False
                summary_collector["errors"].append("Missing target-file")

            # Check desired-tag
            if "desired-tag" not in entry or ("desired-tag" in entry and entry["desired-tag"] is None):
                self._success = False
                summary_collector["errors"].append("Missing desired-tag")

            # Check notify-email
            if "notify-email" not in entry or ("notify-email" in entry and entry["notify-email"] is None):
                self._success = False
                summary_collector["errors"].append("Missing notify-email")

            # Check depends-on
            if "depends-on" not in entry:
                self._success = False
                summary_collector["errors"].append("Missing depends-on")

        return self._success


class IndexProjectsValidator(Validator):
    """Does deeper analysis of index, checking for correctness of provided values."""

    def __init__(self, index_file):

        Validator.__init__(self, index_file)

    @staticmethod
    def _update_git_url(git_url, git_branch):

        clone_path = None

        # Work out the path to clone repo to
        clone_to = git_url

        if ":" in clone_to:
            clone_to = clone_to.split(":")[1]

        clone_to = GlobalEnvironment.environment.repo_dump + "/" + clone_to

        # If the path doesnt allready exist, attempt to clone repo
        if not path.exists(clone_to):
            cmd = ["git", "clone", git_url, clone_to]

            if not execute_command(cmd):
                return None

        # Update repo
        get_back = getcwd()
        chdir(clone_to)

        cmd = "git branch -r | grep -v '\->' | while read remote; do git branch --track \"${remote#origin/}\"" \
              " \"$remote\" &> /dev/null; done"

        # Get all the branches
        system(cmd)

        # fetch the branches
        cmd = ["git", "fetch", "--all"]
        execute_command(cmd)

        # Pull for update
        cmd = ["git", "pull", "--all"]
        execute_command(cmd)

        # Checkout required branch
        cmd = ["git", "checkout", "origin/" + git_branch]

        if execute_command(cmd):
            clone_path = clone_to

        chdir(get_back)

        return clone_path

    def run(self):

        container_names = {}

        for entry in self._yaml:

            summary_collector = Summary.get_summary_collector(self._file_name, entry)

            clone_path = self._update_git_url(entry["git-url"], entry["git-branch"])

            if clone_path is None:
                self._success = False
                summary_collector["errors"].append(
                    "Could not clone specified git-url or could not find specified branch")
                continue

            # Else clone was success, check the git path
            git_path = clone_path + "/" + entry["git-path"]

            # Check if specified path exists
            if not path.exists(git_path):
                self._success = False
                summary_collector["errors"].append("The specified git-path does not exist in git repo.")
                continue

            # Else, continue with remaining checks
            cccp_yml_path = None

            # * Check if cccp.yml file exists

            for item in ["cccp.yml", ".cccp.yml", "cccp.yaml", ".cccp.yaml"]:
                check_path = git_path + "/" + item
                if path.exists(check_path):
                    cccp_yml_path = check_path
                    break

            if cccp_yml_path is None:
                self._success = False
                summary_collector["errors"].append("Missing cccp yml file, please check your git-path")
                continue

            # * Check for duplicate entry for same container name
            container_name = entry["app-id"] + "/" + entry["job-id"] + ":" + str(entry["desired-tag"])
            if container_name in container_names:
                self._success = False
                summary_collector["errors"].append(
                    "Duplicate entry exists at ids : " + str(container_names[container_name]))

            else:
                container_names[container_name] = []

            container_names[container_name].append(entry["id"])

            # * Check for existence of target-file
            if not path.exists(git_path + "/" + entry["target-file"]):
                self._success = False
                summary_collector["errors"].append("The specified target-file does not exist at the git-path")

            # * Validate the cccp yaml file
            self._cccp_yaml_check(git_path, cccp_yml_path, entry, summary_collector)

        return self._success

    def _cccp_yaml_check(self, git_path, cccp_yaml_path, entry, summary_collector):
        """Validates the cccp yaml file"""

        with open(cccp_yaml_path, "r") as cccp_yaml_file:
            cccp_yaml = load(cccp_yaml_file)

        get_back = getcwd()
        chdir(git_path)
        # * Check for job-id
        if "job-id" not in cccp_yaml:
            self._success = False
            summary_collector["errors"].append("Missing job-id field in cccp yaml")

        # * Check for test-skip
        if "test-skip" in cccp_yaml:
            value = cccp_yaml["test-skip"]

            try:
                if value is True or value is False:
                    pass
            except Exception:
                self._success = False
                summary_collector["errors"].append("test-skip should either be True or False as it is a flag")

        # * Check test-script
        if "test-script" in cccp_yaml:
            summary_collector["warnings"].append("Custom test-script has been specified")
            value = str(cccp_yaml["test-script"])
            if not path.exists(value):
                self._success = False
                summary_collector["errors"].append("The specified test-script does not exist")

        # * Check build-script
        if "build-script" in cccp_yaml:
            summary_collector["warnings"].append("Custom build-script has been specified")
            value = str(cccp_yaml["build-script"])
            if not path.exists(value):
                self._success = False
                summary_collector["errors"].append("The specified build-script does not exist")

        # * Check delivery-script
        if "delivery-script" in cccp_yaml:
            summary_collector["warnings"].append("Custom delivery-script has been specified.")
            value = str(cccp_yaml["delivery-script"])
            if not path.exists(value):
                self._success = False
                summary_collector["errors"].append("The specified delivery-script does not exist")

        chdir(get_back)