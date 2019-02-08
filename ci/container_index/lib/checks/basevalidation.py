"""
This file contains base classes for all the validators.
"""

import os

import ci.container_index.lib.state as state
from ci.container_index.lib.constants import FieldKeys, CheckKeys
from ci.container_index.lib.utils import IndexCIMessage, load_yaml
from ci.container_index.lib.constants import FieldKeys


class Validator(object):
    """
    Validates data, based on provided validation logic
    """

    def __init__(self, validation_data, file_name):
        self.message = IndexCIMessage(validation_data)
        self.validation_data = validation_data
        self.file_name = file_name
        self.file_base_name = os.path.basename(self.file_name)

    def _invalidate(self, err):
        """
        Invalidate the validation, with an error message.
        """
        self.message.success = False
        self.message.errors.append(err)

    def _warn(self, warn):
        """
        Add a warning, to the validation.
        """
        self.message.warnings.append(warn)

    def _perform_validation(self):
        """
        Validation logic of the validator resides here.
        Subclass must override
        """
        raise NotImplementedError

    def validate(self):
        """
        Runs the validator to validate based on provided data.
        :return: Returns a flag to indicate success or failure
        and an IndexCIMessage object.
        """
        self._perform_validation()
        return self.message


class BasicSchemaValidator(Validator):
    """
    Acts as parent of all Schema validators classes
    """

    def __init__(self, validation_data, file_name):
        super(BasicSchemaValidator, self).__init__(validation_data, file_name)
        self.field_name = ""

    def _perform_validation(self):
        if not self.validation_data.get(self.field_name):
            self._invalidate(
                str.format(
                    "Missing required field {}",
                    self.field_name
                )
            )
            return
        self._extra_validation()

    def _extra_validation(self):
        """
        This function can be overriden to add more schema validations
        that will need to be done.
        """
        pass


class StringFieldValidator(BasicSchemaValidator):
    """
    Acts as base for all validators that do string validation
    """

    def __init__(self, validation_data, file_name):
        super(StringFieldValidator, self).__init__(validation_data, file_name)
        self.field_name = "UNKNOWN"

    def _extra_validation_1(self):
        """
        This function can be overridden to add any extra validations
        """
        pass

    def _extra_validation(self):
        if not isinstance(
                self.validation_data.get(self.field_name), str
        ):
            self._invalidate(
                str.format(
                    "{} field must be a string",
                    self.field_name
                )
            )
            return
        if len(self.validation_data.get(self.field_name)) <= 0:
            self._invalidate(
                str.format(
                    "{} field cannot be a zero length string",
                    self.field_name
                )
            )
            return
        self._extra_validation_1()


class StateValidator(Validator):
    """
    Acts as parent for stateful validations.
    Note: If you are using any of these classes
    individually, please do a state.init() before and
    state.clean_up() after, from ci.container_index.state
    """

    def __init__(self, validation_data, file_name):
        super(StateValidator, self).__init__(
            validation_data, file_name
        )
        self.state = self.validation_data.get(CheckKeys.STATE)

    def _stateful_validation(self):
        """
        Override to add any more required validation.
        """
        pass

    def _perform_validation(self):
        self._stateful_validation()
        self.state.save()


class OptionalClonedValidator(StateValidator):
    """
    This class contains logic to either optionally clone repo, using git-url
    or to use existing cloned code to perform validation.
    """

    def __init__(self, validation_data, file_name):
        super(OptionalClonedValidator, self).__init__(
            validation_data, file_name
        )
        self.message.title = "Optional Cloned Validator"
        self.clone = None
        self.clone_location = None

    def _clone_repo(self):
        """
        This function clones the git-url and checks out specified git branch.
        """
        self.state.set_git_env()
        self.clone_location = self.state.git_update(
            self.validation_data.get(FieldKeys.GIT_URL),
            self.validation_data.get(FieldKeys.GIT_BRANCH)
        )
        self.state.unset_git_env()

    def _validate_after(self):
        """
        Override to add validations to be done after
        """
        pass

    def _stateful_validation(self):
        # Clone the repo, if needed
        self.clone = self.validation_data.get(CheckKeys.CLONE)
        if not self.clone:
            self.clone_location = self.validation_data.get(
                CheckKeys.CLONE_LOCATION
            )
        else:
            self._clone_repo()
        self._validate_after()


class CCCPYamlValidator(OptionalClonedValidator):
    """
    This class acts as a base class for doing all validations w.r.t cccp yaml.
    """
    def __init__(self, validation_data, file_name):
        super(CCCPYamlValidator, self).__init__(validation_data, file_name)
        self.message.title = "CCCP Yaml Validator"
        self._cccp_yaml_data = None
        self._load_error = None

    def _load_cccp_yaml(self):
        """
        Loads the cccp yaml data, assuming it can find the file
        """
        cccp_dir = str.format(
            "{}/{}",
            self.clone_location,
            self.validation_data.get(FieldKeys.GIT_PATH)
        )
        for p in [
            os.path.join(cccp_dir, "cccp.yml"),
            os.path.join(cccp_dir, ".cccp.yml"),
            os.path.join(cccp_dir, "cccp.yaml"),
            os.path.join(cccp_dir, ".cccp.yaml")
        ]:
            if os.path.exists(p):
                self._cccp_yaml_data, self._load_error = load_yaml(p)
                break

    def _validate_cccp_yaml(self):
        """
        Perform validation, after loading cccp yaml data
        """
        pass

    def _validate_after(self):
        if (FieldKeys.PREBUILD_CONTEXT in self.validation_data and
                FieldKeys.PREBUILD_SCRIPT in self.validation_data):
            self._warn(
                "Skipping checking for cccp yaml as prebuild may be generating"
                " it"
            )
            return
        self._load_cccp_yaml()
        if self._load_error:
            self._invalidate(
                str.format(
                    "Failed to load the cccp data, error : {}",
                )
            )
            return
        else:
            if not self._cccp_yaml_data:
                self._invalidate(
                    str.format(
                        "Failed to find cccp data at {}",
                        self.validation_data.get(FieldKeys.GIT_PATH)
                    )
                )
                return
        self._validate_cccp_yaml()
