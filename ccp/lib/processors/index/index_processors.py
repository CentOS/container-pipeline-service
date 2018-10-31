from glob import glob

from ccp.lib.models.project import Project
from ccp.lib.utils.print_out import print_out
from ccp.lib.utils.parsing import read_yaml


class IndexProcessor(object):
    """
    Class for reading container index and utilities
    """

    def __init__(self, index, namespace):
        """
        Initialize class variable with index location
        """
        self.index = index
        self.namespace = namespace

    def is_valid_entry(self, entry):
        # TODO : Add validation code here
        errors = []
        return errors

    def read_projects(self):
        """
        Reads yaml entries from container index and returns
        them as list of objects of type Project
        """
        projects = []

        for yaml_file in glob(self.index + "/*.y*ml"):
            # skip index_template
            if "index_template" in yaml_file:
                continue

            app = read_yaml(yaml_file)
            # if YAML file reading has failed, log the error and
            # filename and continue processing rest of index
            if not app:
                continue

            for entry in app['Projects']:
                # create a project object here with all properties
                try:
                    errors = self.is_valid_entry(entry)
                    if len(errors) == 0:
                        projects.append(Project(entry, self.namespace))
                    else:
                        print_out("Entry has validation errors : ")
                        for i in errors:
                            print_out("- {}".format(i))
                        print_out("Skipping")
                except Exception as e:
                    print_out("Error processing index entry {}. "
                              "Moving on.".format(entry))
                    print_out("Error: {}".format(e))
        return projects
