import yaml
import os
import sys
from glob import glob

class IndexdTransformer:
    """Class to transform indexd to indexyml"""

    def __init__(self, indexdpath, indexymlpath):

        if not os.path.exists(indexdpath):
            raise ValueError("Invalid path of indexd specified.")

        self._indexd_path = indexdpath
        self._indexyml_path = indexymlpath

        self._munge_db = self._indexd_path + "/" + "index_of_indexes"

    def _gen_indexyml(self):
        """Combines the index.d files into index.yml files"""

        index_files = None

        # Get the list of files form the indexofindexes
        index_files_path = self._indexd_path + "/*.yml"
        index_files = glob(index_files_path)

        # Prepend the Projects tag to the yml file.
        targetfile = open(self._indexyml_path, "w")
        targetfile.write("Projects:\n")

        # Munge all the data from the indexes to the index.yml file
        for ifile in index_files:
            if "index_template" not in ifile:
                with open(ifile, "r") as current_file:
                    targetfile.write(current_file.read())

        targetfile.close()

    def _transform_ids(self):
        """Transforms the ids to a combination of appid_jobid_id"""

        yaml_data = None

        # Read the index.yml files
        with open(self._indexyml_path, "r") as index_yml_file:
            yaml_data = yaml.load(index_yml_file)

        # Go through every entry
        for entry in yaml_data["Projects"]:

            if "app-id" not in entry or "job-id" not in entry:
                raise KeyError("Missing app-id or job-id entry in : \n" + str(entry))

            # Form the new id as combination of app-id_job-id_id
            new_id = entry["app-id"] + "_" + entry["job-id"] + "_" + str(entry["id"])
            entry["id"] = new_id

        with open(self._indexyml_path, "w") as index_yml_file:
            yaml.dump(yaml_data, index_yml_file, default_flow_style=False)

    def _add_comment(self):
        """Prepends a comment line to the index.yml file"""

        orig_data = None

        with open(self._indexyml_path, "r") as indexyml_file:
            orig_data = indexyml_file.read()

        with open(self._indexyml_path, "w") as indexyml_file:
            indexyml_file.write("# This file is auto-generated and managed by container pipeline service\n" + orig_data)

    def run(self):

        self._gen_indexyml()
        self._transform_ids()
        self._add_comment()

if __name__ == '__main__':
   indexd_location =  sys.argv[1]
   indexyml_location = sys.argv[2]

   IndexdTransformer(indexd_location, indexyml_location).run()
