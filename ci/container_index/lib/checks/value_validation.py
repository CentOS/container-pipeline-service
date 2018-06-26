from os import path

from ci.container_index.lib.checks.basevalidation import \
    OptionalClonedValidator


class GitCloneValidator(OptionalClonedValidator):
    def __init__(self, validation_data, file_name):
        super(GitCloneValidator, self).__init__(validation_data, file_name)

    def _validate_after(self):
        self.message.title = "Git Clone Validator"
        if not self.clone_location:
            self._invalidate("Failed to clone git repo or checkout git branch")
            return


class CccpYamlExistsValidator(OptionalClonedValidator):
    def __init__(self, validation_data, file_name):
        super(CccpYamlExistsValidator, self).__init__(
            validation_data, file_name
        )

    def _validate_after(self):
        self.message.title = "CCCP YAML Validator"
        if all(False in s for s in [
            path.exists(path.join(self.clone_location, "cccp.yml")),
            path.exists(path.join(self.clone_location, ".cccp.yml")),
            path.exists(path.join(self.clone_location, "cccp.yaml")),
            path.exists(path.join(self.clone_location, ".cccp.yaml"))
        ]):
            self._invalidate("CCCP yaml file does not exist in repository.")
            return
