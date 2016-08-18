import os


class Globals:
    """Contains the stuff that needs to be accessible by everyone"""

    index_git = "https://github.com/CentOS/container-index.git"
    index_git_branch = "master"
    index_location = ""
    custom_index_location = None

    data_dump_directory = ""
    index_directory = ""
    index_file = ""
    repo_directory = ""
    tests_directory = ""

    custom_index_file_indicator = ""
    previous_index_git_file = ""

    build_info = ""
    old_environ = None
    indexd_indexyml_transformer_path = os.path.abspath("../jenkinsbuilder/indexdindexymltransform.py")

    @staticmethod
    def setdatadirectory(value):

        if not os.path.isabs(value):
            value = os.path.abspath(value)

        Globals.data_dump_directory = value
        Globals.index_directory = value + "/index"
        Globals.index_file = Globals.index_directory + "/index.yml"
        Globals.index_location = Globals.index_directory + "/index.d"
        Globals.repo_directory = value + "/repos"
        Globals.tests_directory = value + "/tests"
        Globals.custom_index_file_indicator = value + "/.customindex"
        Globals.previous_index_git_file = value + "/.indexgit"
        Globals.build_info = value + "/builds.info"

        return
