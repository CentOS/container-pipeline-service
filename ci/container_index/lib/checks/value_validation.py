"""
This file contains validators that check for validity of values provided in the
index
"""
from os import path

from ci.container_index.lib.checks.basevalidation import \
    OptionalClonedValidator, CCCPYamlValidator
from ci.container_index.lib.constants import *


class GitCloneValidator(OptionalClonedValidator):
    """
    Validates if git repo is clonable and requisite branch can be checked out.
    """
    def __init__(self, validation_data, file_name):
        super(GitCloneValidator, self).__init__(validation_data, file_name)

    def _validate_after(self):
        self.message.title = "Git Clone Validator"
        if not self.clone_location:
            self._invalidate("Failed to clone git repo or checkout git branch")
            return


class CCCPYamlExistsValidator(CCCPYamlValidator):
    """
    Validates if cccp yaml file exists or not
    """
    def __init__(self, validation_data, file_name):
        super(CCCPYamlExistsValidator, self).__init__(
            validation_data, file_name
        )
        self.message.title = "CCCP Yaml Exists Validator"


class TargetFileExistsValidator(OptionalClonedValidator):
    """
    Validates if target-file exists at specified location
    """
    def __init__(self, validation_data, file_name):
        super(TargetFileExistsValidator, self).__init__(
            validation_data, file_name
        )

    def _validate_after(self):
        self.message.title = "Target File Exists Validator"
        if FieldKeys.PREBUILD_SCRIPT in self.validation_data:
            self._warn("Skipping target file check as prebuild step exists")
            return
        if (not path.exists(
            str.format(
                "{}/{}/{}",
                self.clone_location,
                self.validation_data.get(FieldKeys.GIT_PATH),
                self.validation_data.get(FieldKeys.TARGET_FILE)
             ))):
            self._invalidate(
                str.format(
                    "Target File {} does not exist, at the path {}",
                    self.validation_data.get(FieldKeys.TARGET_FILE),
                    self.validation_data.get(FieldKeys.GIT_PATH)
                )
            )
            return


class PreBuildExistsValidator(OptionalClonedValidator):
    """
    Checks if prebuild data is valid.
    """
    def __init__(self, validation_data, file_name):
        super(PreBuildExistsValidator, self).__init__(
            validation_data, file_name
        )

    def _validate_after(self):
        self.message.title = "Prebuild Exists Validator"
        if FieldKeys.PREBUILD_SCRIPT not in self.validation_data:
            return
        if (FieldKeys.PREBUILD_SCRIPT in self.validation_data and
                FieldKeys.PREBUILD_CONTEXT not in self.validation_data):
            self._invalidate(
                "Prebuild script is provided, but no prebuild context"
            )
            return

        if (not path.exists(
                str.format(
                    "{}/{}",
                    self.clone_location,
                    self.validation_data.get(FieldKeys.PREBUILD_CONTEXT)
                )
        )):
            self._invalidate(
                str.format(
                    "Prebuild context does not exist at {}",
                    self.validation_data.get(FieldKeys.PREBUILD_CONTEXT)
                )
            )
        if (not path.exists(
                str.format(
                    "{}/{}/{}",
                    self.clone_location,
                    self.validation_data.get(FieldKeys.PREBUILD_CONTEXT),
                    self.validation_data.get(FieldKeys.PREBUILD_SCRIPT)
                )
        )):
            self._invalidate(
                str.format(
                    "Prebuild script does not exist at {}/{}",
                    self.validation_data.get(FieldKeys.PREBUILD_CONTEXT),
                    self.validation_data.get(FieldKeys.PREBUILD_SCRIPT)
                )
            )


class JobIDMatchesIndex(CCCPYamlValidator):
    """
    Checks if Job id in cccp yaml is same as in index
    """

    def __init__(self, validation_data, file_name):
        super(JobIDMatchesIndex, self).__init__(validation_data, file_name)
        self.message.title = "CCCP Job id matches index"

    def _validate_cccp_yaml(self):
        cccp_jid = self._cccp_yaml_data.get(FieldKeys.JOB_ID)
        if not cccp_jid:
            self._invalidate("job-id must be present in the cccp yaml file")
            return
        if cccp_jid and cccp_jid != self.validation_data.get(FieldKeys.JOB_ID):
            self._invalidate("job-id does not match value provided in index.")
            return
