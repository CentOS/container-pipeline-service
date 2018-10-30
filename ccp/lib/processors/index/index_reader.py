from glob import glob

from ccp.lib.models.project import Project
from ccp.lib.utils.print_out import print_out
from ccp.lib.utils.parsing import read_yaml


class IndexReader(object):
    """
    Class for reading container index and utilities
    """

    def __init__(self, index, namespace):
        """
        Initialize class variable with index location
        """
        self.index = index
        self.namespace = namespace

    def read_projects(self):
        """
        Reads yaml entries from container index and returns
        them as list of objects of type Project
        """
        projects = []

        for yamlfile in glob(self.index + "/*.y*ml"):
            # skip index_template
            if "index_template" in yamlfile:
                continue

            app = read_yaml(yamlfile)
            # if YAML file reading has failed, log the error and
            # filename and continue processing rest of index
            if not app:
                continue

            for entry in app['Projects']:
                # create a project object here with all properties
                try:
                    project = Project(entry, self.namespace)
                except Exception as e:
                    print_out("Error processing index entry {}. "
                           "Moving on.".format(entry))
                    print_out("Error: {}".format(e))
                else:
                    # append to the list of projects
                    projects.append(project)
        return projects
