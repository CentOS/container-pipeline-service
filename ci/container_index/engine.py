import ci.container_index.lib.checks.schema_validation as schema_validation
import ci.container_index.config as config

import ci.container_index.lib.utils as utils
import ci.container_index.lib.constants as constants

from os import mkdir, rmdir, path
from glob import glob

class Engine(object):
    """
    This class controls the flow of ci runs.
    """

    def _load_validators(self, v_type, v_list):
        """
        Loads a list of validators, using reflection.
        """
        for v in v_list:
            self.validators.append(
                getattr(v_type, v)
            )

    def __init__(
        self, schema_validators=None,
        value_validators=None, index_location="./", verbose=True
    ):
        """
        Initializes the test engine
        """
        self.verbose = verbose
        # Index file location needs to be provided
        if not path.exists(index_location):
            raise Exception(
                "Could not find location specified for index."
            )

        # Goto the index location and collect the index files
        self.index_location = path.abspath(index_location)
        self.index_d = path.join(self.index_location, "index.d")
        self.index_files = glob(
            str.format("{}/*.y*ml", self.index_d)
        )

        if (len(self.index_files) == 0 or
           (len(self.index_files) == 1 and
               any("index_template" in s for s
                   in self.index_files))):
            raise Exception("No index files to process.")

        # Collect the validators that need to run.
        self.validators = []
        # - Schema Validators:
        if (not schema_validators or not
           isinstance(schema_validators, list) or
           len(schema_validators) <= 0):
            v_list = config.schema_validators
        else:
            v_list = schema_validators
        self._load_validators(schema_validation, v_list)

        # - Value Validators
        # TODO

        self.summary = {}

    def add_summary(self, file_name, messages):
        """
        Adds a summary.
        """
        self.summary[file_name] = messages

    def run(self):
        """
        Runs the index ci tests.
        """
        overall_success = True
        for index_file in self.index_files:
            file_data, err = utils.load_yaml(index_file)
            if file_data:
                messages = []

                # Perform primary validation
                m = schema_validation.TopLevelProjectsValidator(
                    file_data, index_file
                ).validate()
                messages.append(m)
                # If primary validation was successful, move forward.
                if m.success:
                    entries = file_data.get(constants.FieldKeys.PROJECTS)
                    # Extract entries and start evaluating them, one by one
                    for entry in entries:
                        for v in self.validators:
                            m = v(entry, index_file).validate()
                            if not m.success:
                                overall_success = False
                            messages.append(m)
                else:
                    overall_success = False
            else:
                utils.print_out(
                    "Could not fetch data from index file {}\nError:{}".format(index_file, err),
                    verbose=self.verbose
                )

            self.add_summary(index_file, messages)

        return overall_success, self.summary
