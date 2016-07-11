import os


class Globals:
    """Contains the stuff that needs to be accessible by everyone"""

    indexGit = "https://github.com/kbsingh/cccp-index.git"
    customIndexFile = None

    dataDumpDirectory = ""
    indexDirectory = ""
    indexFile = ""
    repoDirectory = ""
    testsDirectory = ""

    customindexfileindicator = ""
    previousIndexGitFile = ""

    buildinfo = ""

    @staticmethod
    def setdatadirectory(value):
        if not os.path.isabs(value):
            value = os.path.abspath(value)

        Globals.dataDumpDirectory = value
        Globals.indexDirectory = value + "/index"
        Globals.indexFile = Globals.indexDirectory + "/index.yml"
        Globals.repoDirectory = value + "/repos"
        Globals.testsDirectory = value + "/tests"
        Globals.customindexfileindicator = value + "/.customindex"
        Globals.previousIndexGitFile = value + "/.indexgit"
        Globals.buildinfo = value + "/builds.info"

        return
