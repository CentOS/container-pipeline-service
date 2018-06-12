from ci.container_index.lib.checks.basevalidation\
    import Validator, BasicSchemaValidator, StringFieldValidator
import ci.container_index.lib.utils as index_utils
from ci.container_index.lib.constants import *
from os.path import realpath, dirname, join
from uuid import uuid4
from ci.container_index.lib.utils import\
    load_yaml, dump_yaml


def gen_tracking_file():
    dir_path = dirname(realpath(__file__))
    return join(
        dir_path,
        ".track_file_" + str(uuid4())
    )


class TopLevelProjectsValidator(Validator):

    def __init__(self, validation_data, file_name):
        super(TopLevelProjectsValidator, self).__init__(
            validation_data, file_name)

    def _perform_validation(self):
        self.message.title = "Top level projects"
        if not self.validation_data.get(
            FieldKeys.PROJECTS
        ):
            self._invalidate(
                "Index data should begin with "
                "top level \"Projects:\""
            )
            return
        if not isinstance(
            self.validation_data.get(FieldKeys.PROJECTS),
            list
        ):
            self._invalidate(
                "Projects must be provided as a list of dicts."
            )
            return


class IDValidator(BasicSchemaValidator):

    def __init__(self, validation_data, file_name):
        super(IDValidator, self).__init__(
            validation_data, file_name)
        self.field_name = FieldKeys.ID

    def _extra_validation(self):
        self.message.title = "Id field validation"
        if not isinstance(
            self.validation_data.get(FieldKeys.ID), int
        ):
            self._invalidate("id field must be an integer.")
            return


class AppIDValidator(StringFieldValidator):

    def __init__(self, validation_data, file_name):
        super(AppIDValidator, self).__init__(
            validation_data, file_name)
        self.field_name = FieldKeys.APP_ID
        self.message.title = "App ID Validation"

    def _extra_validation_1(self):
        if (self.validation_data.get(self.field_name) !=
           self.file_base_name.split(".")[0]):
            self._invalidate(
                str.format(
                    "{} must be the same as the file name",
                    self.field_name
                )
            )
            return


class JobIDValidator(StringFieldValidator):

    def __init__(self, validation_data, file_name):
        super(JobIDValidator, self). __init__(
            validation_data, file_name)
        self.field_name = FieldKeys.JOB_ID
        self.message.title = "Job ID Validation"


class DesiredTagValidator(StringFieldValidator):

    def __init__(self, validation_data, file_name):
        super(DesiredTagValidator, self).__init__(
            validation_data, file_name)
        self.field_name = FieldKeys.DESIRED_TAG
        self.message.title = "Desired Tag Validation"


class GitURLValidator(StringFieldValidator):

    def __init__(self, validation_data, file_name):
        super(GitURLValidator, self).__init__(
            validation_data, file_name)
        self.field_name = FieldKeys.GIT_URL
        self.message.title = "Git URL Validation"


class GitPathValidator(StringFieldValidator):

    def __init__(self, validation_data, file_name):
        super(GitPathValidator, self).__init__(
            validation_data, file_name)
        self.field_name = FieldKeys.GIT_PATH
        self.message.title = "Git Path Validation"


class GitBranchValidator(StringFieldValidator):

    def __init__(self, validation_data, file_name):
        super(GitBranchValidator, self).__init__(
            validation_data, file_name)
        self.field_name = FieldKeys.GIT_BRANCH
        self.message.title = "Git Branch Validation"


class TargetFileValidator(StringFieldValidator):

    def __init__(self, validation_data, file_name):
        super(TargetFileValidator, self).__init__(
            validation_data, file_name)
        self.field_name = FieldKeys.TARGET_FILE
        self.message.title = "Target File Validation"


class NotifyEmailValidator(StringFieldValidator):

    def __init__(self, validation_data, file_name):
        super(NotifyEmailValidator, self).__init__(
            validation_data, file_name)
        self.field_name = FieldKeys.NOTIFY_EMAIL
        self.message.title = "Notify Email Validation"


class BuildContextValidator(StringFieldValidator):

    def __init__(self, validation_data, file_name):
        super(BuildContextValidator, self).__init__(
            validation_data, file_name)
        self.field_name = FieldKeys.BUILD_CONTEXT
        self.message.title = "Build Context Validation"
