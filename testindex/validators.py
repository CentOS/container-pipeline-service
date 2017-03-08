import re
from os import path, getcwd, chdir, system

from yaml import load

from nuts_and_bolts import execute_command, calculate_repo_path
from summary import SummaryCollector


class Validator(object):
    """Base class for all validators"""

    def __init__(self, context):
        """
        Initialize a validator
        Keyword arguments:
            context -- nuts_and_bolts.Context object that holds the global information
            such as environment, summary and Dependency Validator
        """
        self._success = True
        self._summary_collector = None
        self._context = context
        pass

    @staticmethod
    def _load_yml(file_name):
        """
        Loads yml data into a yaml.load object and returns it.
        None and exception object is returned if load failed.
        Keyword arguments:
            file_name -- The path of the yml file to load
        """

        try:
            with open(file_name, "r") as yml_file:
                return load(yml_file), None
        except Exception as e:
            return None, e

    def run(self):
        """"Runs the validator. returning True or False based on success or failure"""
        raise NotImplementedError("Implement this method")


class RegexPatterns(object):
    """Static class holds pre-compiled regular expression matchers"""

    # This matches the full name of container to [regurl]/namespace/container:tag
    container_full_name = re.compile("^(([0-9a-zA-Z_-]+[.]{1})*([0-9a-zA-Z_-]+){1}[/]{1})?[0-9a-zA-Z_-]+[/]{1}"
                                     "[0-9a-zA-Z_-]+[:]{1}([0-9a-zA-Z_-]+\.?)+$")


class IndexValidator(Validator):
    """Top level class for index validators"""

    def __init__(self, context, index_file):
        """
        Initialize the IndexValidator object
        Keyword arguments:
            context -- nuts_and_bolts.Context object that holds the global information
            such as environment, summary and Dependency Validator.
            index_file -- The path of the index.d file that is to be validated
        """
        Validator.__init__(self, context=context)
        self._file_name = path.basename(index_file)
        self._index_file = index_file
        temp_index_data, ex = self._load_yml(self._index_file)
        self._entry = None

        if temp_index_data:
            if "Projects" in temp_index_data:
                self._index_data = temp_index_data["Projects"]
            else:
                self._success = False
                self._context.summary.global_errors.append("Projects absent in " + self._index_file)
        else:
            self._success = False
            self._context.summary.global_errors.append("Malformed " + path.basename(self._index_file) + " : " + str(ex))
        self._status_list = {
            "fail": [],
            "success": []
        }

    def _mark_entry_status(self, valid=True):
        """
        Marks an entry as valid or invalid
        Keyword arguments:
            entry -- The index entry that needs to be marked as valid or invalid.
            valid -- The flag to indicate weather to mark entry as valid or invalid
        """
        if valid:
            if self._entry in self._status_list["fail"]:
                self._status_list["fail"].remove(self._entry)
            if self._entry not in self._status_list["success"]:
                self._status_list["success"].append(self._entry)
        else:
            if self._entry in self._status_list["success"]:
                self._status_list["success"].remove(self._entry)
            if self._entry not in self._status_list["fail"]:
                self._status_list["fail"].append(self._entry)

    def run(self):
        raise NotImplementedError("Implement this method.")


class IndexFormatValidator(IndexValidator):
    """Checks the format of index files"""

    def __init__(self, context, index_file):
        """
        Initialize this validator
        Keyword arguments:
            context --  nuts_and_bolts.Context object that holds the global information
            index_file -- The index file to be validated
        """
        IndexValidator.__init__(self, context, index_file)

    def run(self):
        if not self._success:
            return False, self._status_list

        id_list = []

        for self._entry in self._index_data:

            self._summary_collector = SummaryCollector(self._context, self._file_name, self._entry)
            self._mark_entry_status(valid=True)

            # Check if id field exists
            if "id" not in self._entry or ("id" in self._entry and self._entry["id"] is None):
                self._mark_entry_status(valid=False)
                self._summary_collector.add_error("Missing id")

            else:
                # Check if id has not already been passed
                if self._entry["id"] in id_list:
                    self._mark_entry_status(valid=False)
                    self._summary_collector.add_error("id field must be unique in the file")

                else:
                    id_list.append(self._entry["id"])

            # Checking app-id field
            if "app-id" not in self._entry or ("app-id" in self._entry and self._entry["app-id"] is None):
                self._mark_entry_status(valid=False)
                self._summary_collector.add_error("Missing app-id")

            else:
                if self._entry["app-id"] != self._file_name.split(".")[0]:
                    self._summary_collector.add_warning("app-id should be same as first part of the file name")

                if "_" in self._entry["app-id"] or "/" in self._entry["app-id"] or "." in self._entry["app-id"]:
                    self._mark_entry_status(valid=False)
                    self._summary_collector.add_error("app-id cannot contain _, / or . character.")

            # Checking job-id field
            if "job-id" not in self._entry or ("job-id" in self._entry and self._entry["job-id"] is None):
                self._mark_entry_status(valid=False)
                self._summary_collector.add_error("Missing job-id field")

            else:
                try:
                    int(self._entry["job-id"])
                    self._mark_entry_status(valid=False)
                    self._summary_collector.add_error("Job id must be a string")
                except ValueError:
                    pass
                if "_" in self._entry["job-id"] or "/" in self._entry["job-id"] or "." in self._entry["job-id"]:
                    self._mark_entry_status(valid=False)
                    self._summary_collector.add_error("job-id cannot contain _, / or . character.")

            # Check for git-url
            if "git-url" not in self._entry or ("git-url" in self._entry and self._entry["git-url"] is None):
                self._mark_entry_status(valid=False)
                self._summary_collector.add_error("Missing git-url")

            # Checking git-path
            if "git-path" not in self._entry or ("git-path" in self._entry and self._entry["git-path"] is None):
                self._mark_entry_status(valid=False)
                self._summary_collector.add_error("Missing git-path")

            # Check git-branch
            if "git-branch" not in self._entry or ("git-branch" in self._entry and self._entry["git-branch"] is None):
                self._mark_entry_status(valid=False)
                self._summary_collector.add_error("Missing git-branch")

            # Check target-file
            if "target-file" not in self._entry or ("target-file" in self._entry and self._entry["target-file"] is None):
                self._mark_entry_status(valid=False)
                self._summary_collector.add_error("Missing target-file")

            # Check desired-tag
            if "desired-tag" not in self._entry or ("desired-tag" in self._entry and self._entry["desired-tag"] is None):
                self._mark_entry_status(valid=False)
                self._summary_collector.add_error("Missing desired-tag")

            # Check notify-email
            if "notify-email" not in self._entry or ("notify-email" in self._entry and self._entry["notify-email"] is None):
                self._mark_entry_status(valid=False)
                self._summary_collector.add_error("Missing notify-email")

            # Check depends-on
            if "depends-on" not in self._entry:
                self._mark_entry_status(valid=False)
                self._summary_collector.add_error("Missing depends-on")
            elif self._entry["depends-on"]:
                depends_on = self._entry["depends-on"]
                if not isinstance(depends_on, list):
                    depends_on = [depends_on]
                for item in depends_on:
                    if not RegexPatterns.container_full_name.search(str(item)):
                        self._mark_entry_status(valid=False)
                        self._summary_collector.add_error("Depends on entry pattern mismatch found {0} must be"
                                                          " <string>/<string>:<string>, ".format(str(item)))

        if len(self._status_list["fail"]):
            self._success = False
        return self._success, self._status_list


class IndexProjectsValidator(IndexValidator):
    """Does deeper analysis of index, checking for correctness of provided values."""

    def __init__(self, context, index_file):
        """
        Initialize this validator
        Keyword arguments:
            context -- nuts_and_bolts.Context object that holds the global information
            index_file -- The index file to be validated
        """
        IndexValidator.__init__(self, context, index_file)

    @staticmethod
    def update_git_url(repo_dump, git_url, git_branch):
        """
        Clones the git repo to appropriate location, checks out the appropriate branch and returns the path of clone.
        It returns None on failure.
        Keyword arguments:
            repo_dump -- The location on disk where the git repos will be dumped
            git_url -- The git url to clone.
            git_branch -- The git branch to checkout.
        """

        clone_path = None

        # Work out the path to clone repo to
        clone_to = calculate_repo_path(git_url, git_path=None, repo_dump=repo_dump)[0]

        # If the path doesnt already exist, attempt to clone repo
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
        if not self._success:
            return False, self._status_list

        container_names = {}

        for self._entry in self._index_data:
            self._mark_entry_status(valid=True)
            self._summary_collector = SummaryCollector(self._context, self._file_name, self._entry)

            clone_path = self.update_git_url(self._context.environment.repo_dump, self._entry["git-url"],
                                             self._entry["git-branch"])

            if clone_path is None:
                self._mark_entry_status(valid=False)
                self._summary_collector.add_error(
                    "Could not clone specified git-url or could not find specified branch")
                continue

            # Else clone was success, check the git path
            git_path = clone_path + "/" + self._entry["git-path"]

            # Check if specified path exists
            if not path.exists(git_path):
                self._mark_entry_status(valid=False)
                self._summary_collector.add_error("The specified git-path does not exist in git repo.")
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
                self._mark_entry_status(valid=False)
                self._summary_collector.add_error("Missing cccp yml file, please check your git-path")
                continue

            # * Check for duplicate entry for same container name
            container_name = self._entry["app-id"] + "/" + self._entry["job-id"] + ":" + str(self._entry["desired-tag"])
            if container_name in container_names:
                self._mark_entry_status(valid=False)
                self._summary_collector.add_error(
                    "Duplicate entry exists at ids : " + str(container_names[container_name]))

            else:
                container_names[container_name] = []

            container_names[container_name].append(self._entry["id"])

            # * Check for existence of target-file
            if not path.exists(git_path + "/" + self._entry["target-file"]):
                self._mark_entry_status(valid=False)
                self._summary_collector.add_error("The specified target-file does not exist at the git-path")

            # * Validate the cccp yml file
            self._cccp_yml_check(git_path, cccp_yml_path)

        if len(self._status_list["fail"]) > 0:
            self._success = False
        return self._success, self._status_list

    def _cccp_yml_check(self, clone_path, cccp_yaml_path):
        """
        Validates the cccp yaml file
        Keyword arguments:
            clone_path -- The path of the directory where targetfile, and cccp.yml are present
            cccp_yaml_path -- The path of the cccp yaml file
            entry -- The entry to be validated (needed by entry status marker)
        """

        temp_cccp, ex = self._load_yml(cccp_yaml_path)
        if not temp_cccp:
            self._mark_entry_status(valid=False)
            self._summary_collector.add_error("Malformed cccp yml : " + str(ex))
        cccp_yaml = temp_cccp

        get_back = getcwd()
        chdir(clone_path)
        # * Check for job-entry_id
        if "job-id" not in cccp_yaml:
            self._mark_entry_status(valid=False)
            self._summary_collector.add_error("Missing job-id field in cccp yaml")

        # * Check for test-skip
        if "test-skip" in cccp_yaml:
            value = cccp_yaml["test-skip"]

            try:
                if value and (value is True or value is False):
                    pass
                if value is None:
                    self._summary_collector.add_warning("Optional test-skip is set None, which means its value will be"
                                                        " ignored")
            except Exception as ex:
                self._mark_entry_status(valid=False)
                self._summary_collector.add_error("test-skip should either be True or False as it is a flag")

        # * Check test-script
        if "test-script" in cccp_yaml:
            self._summary_collector.add_warning("Custom test-script has been specified")
            value = cccp_yaml["test-script"]
            value1 = cccp_yaml["test-skip"]
            if value1 is None and value:
                self._summary_collector.add_warning("test-script will be skipped as test-skip is defaulted to True")
            if value1 is not None and value1 is True:
                self._summary_collector.add_warning("test-script will be skipped as test-skip is set to true")
            if value and not path.exists(str(value)):
                self._mark_entry_status(valid=False)
                self._summary_collector.add_error("The specified test-script does not exist")
            if value is None:
                self._summary_collector.add_warning("Optional test-script has a value of None, which means it will be"
                                                    " ignored")

        # * Check build-script
        if "build-script" in cccp_yaml:
            self._summary_collector.add_warning("Custom build-script has been specified")
            value = cccp_yaml["build-script"]
            if value and not path.exists(str(value)):
                self._mark_entry_status(valid=False)
                self._summary_collector.add_error("The specified build-script does not exist")
            if value is None:
                self._summary_collector.add_warning("Optional build-script has has a value None, which means it will be"
                                                    " ignored")

        # * Check delivery-script
        if "delivery-script" in cccp_yaml:
            self._summary_collector.add_warning("Custom delivery-script has been specified.")
            value = cccp_yaml["delivery-script"]
            if value and not path.exists(str(value)):
                self._mark_entry_status(valid=False)
                self._summary_collector.add_error("The specified delivery-script does not exist")
            if value is None:
                self._summary_collector.add_warning("Optional delivery script has value None, which means it will be"
                                                    " ignored")

        chdir(get_back)


class DependencyValidationUpdater(IndexValidator):
    """This script reads the index file and updates the dependency graph, created nodes and edges, for containers and
    dependencies respectively."""

    def __init__(self, context, index_file):
        """Initialize the validator"""

        IndexValidator.__init__(self, context, index_file)

    def run(self):
        """Run the validator the read the index and update the dependency graph"""

        if not self._success:
            return False

        for self._entry in self._index_data:
            # Form the container name from index yaml
            primary_container_name = str(self._entry["app-id"]) + "/" + str(self._entry["job-id"]) + ":" + \
                                     str(self._entry["desired-tag"])
            # Add the container to dependency graph (if it does not already exist)
            self._context.dependency_validator.dependency_graph.add_container(primary_container_name, from_index=True)
            # Check if entry has any dependencies to account for
            if self._entry["depends-on"]:
                if not isinstance(self._entry["depends-on"], list):
                    value = [self._entry["depends-on"]]
                else:
                    value = self._entry["depends-on"]
                for item in value:
                    if ":" not in item:
                        item += ":latest"
                    # Add the dependent container to dependency graph, if it does not already exist
                    self._context.dependency_validator.dependency_graph.add_container(str(item), from_index=True)
                    # Ensure that the dependency from current depends-on container and the current container is
                    #  established
                    self._context.dependency_validator.dependency_graph.add_dependency(str(item),
                                                                                       primary_container_name)
            # Work out the path to targetfile
            git_branch = self._entry["git-branch"]
            git_url = self._entry["git-url"]
            git_path = self._entry["git-path"]
            repo_dir, target_file_dir = calculate_repo_path(git_url, git_path=git_path, context=self._context)
            target_file = target_file_dir + "/" + self._entry["target-file"]
            get_back = getcwd()
            chdir(repo_dir)
            # Checkout required branch
            cmd = ["git", "checkout", "origin/" + git_branch]
            execute_command(cmd)
            chdir(get_back)
            base_image = None
            try:
                with open(target_file, "r") as f:
                    for line in f:
                        l = line.strip()
                        if l.startswith("FROM"):
                            base_image = l.split()[1]
                            break
            except Exception as e:
                print e
            if base_image:
                self._context.dependency_validator.dependency_graph.add_container(container_name=base_image,
                                                                                  from_target_file=True)
                self._context.dependency_validator.dependency_graph.add_dependency(base_image, primary_container_name)
        return True


class LightWeightValidator(IndexValidator):
    """Light weight validator does minimum validation, and focuses mostly on building dependency graph"""

    def __init__(self, context, index_file):
        IndexValidator.__init__(self, context, index_file)

    def run(self):
        for entry in self._index_data:
            self._summary_collector = SummaryCollector(self._context, self._file_name, entry)
            if "git-url" not in entry or "git-branch" not in entry or "git-path" not in entry or "target-file" not in \
                    entry:
                self._summary_collector.add_error("Missing git-url, git-path, git-branch or target-file")
                self._success = False
                continue
            clone_location = IndexProjectsValidator.update_git_url(self._context.environment.repo_dump,
                                                                   entry["git-url"], entry["git-branch"])
            if not clone_location:
                self._summary_collector.add_error("Unable to clone specified git-url or find specified git-branch")
                self._success = False
                continue
            validation_path = clone_location + "/" + entry["git-path"] + "/" + entry["target-file"]
            if not path.exists(validation_path):
                self._summary_collector.add_error("Invalid git-path or target-file specified")
                self._success = False

        if self._success:
            DependencyValidationUpdater(context=self._context, index_file=self._index_file).run()
        return self._success
