import os
import shutil

import yaml

import Globals
import NutsAndBolts


class IndexVerifier:
    """This is the first pass of the system, validating the formatting of the index file."""

    def __init__(self):
        """Initialize the verifier"""

        self._logger = NutsAndBolts.Logger(Globals.Globals.dataDumpDirectory + "/index.log")

        return

    def _cleanupIndex(self):
        """Cleans up previous index data"""

        shutil.rmtree(Globals.Globals.indexDirectory)
        os.mkdir(Globals.Globals.indexDirectory)

        return

    def _prepareIndex(self):
        """Prepare the index, by cloning it or copying local index.yml, if specified"""

        success = True

        # Check if custom index file is specified.
        if Globals.Globals.customIndexFile is not None:

            # Clean up previous index
            self._cleanupIndex()

            # Tell the tracker what was just done
            NutsAndBolts.Tracker.setCustomIndexUsed(True)

            # Copy over specified index to where it should be
            shutil.copy2(Globals.Globals.customIndexFile, Globals.Globals.indexFile)

        # Go to the clone index repo way of doing things
        else:

            # print NutsAndBolts.Tracker.getPreviousIndexGit()

            # If custom indexfile is used, or the tracker says current indexgit is not the same as previous one
            if NutsAndBolts.Tracker.isCustomIndexUsed() or \
                            Globals.Globals.indexGit != NutsAndBolts.Tracker.getPreviousIndexGit():

                # Clean up previous.
                self._cleanupIndex()

                # Clone the new index
                cmd = ["git", "clone", Globals.Globals.indexGit, Globals.Globals.indexDirectory]
                NutsAndBolts.Tracker.setPreviousIndexGit(Globals.Globals.indexGit)

                if not NutsAndBolts.StaticHandler.execcmd(cmd):
                    return False

            getback = os.getcwd()
            os.chdir(Globals.Globals.indexDirectory)
            cmd = ["git", "fetch", "--all"]
            NutsAndBolts.StaticHandler.execcmd(cmd)
            checkoutbranch = "origin/" + Globals.Globals.indexgitbranch
            cmd = ["git", "checkout", checkoutbranch]
            success = NutsAndBolts.StaticHandler.execcmd(cmd)
            cmd = ["git", "pull", "--all"]
            NutsAndBolts.StaticHandler.execcmd(cmd)
            os.chdir(getback)

        return success

    def _verifyIndex(self):
        """Does the validation of the index.yml formatting"""

        success = True

        t = None
        idlist = []
        containerlist = []

        # Load the index data
        indexdata = ""

        # Open the index file, and read it
        with open(Globals.Globals.indexFile) as indexfile:
            indexdata = yaml.load(indexfile)

        # Check if projects entry exists
        self._logger.log(NutsAndBolts.Logger.info, "Checking if \"Projects\" entry exists...")

        # Only if 'Projects' entry is found we go ahead. Else it is a failure at this stage itself
        if "Projects" in indexdata.keys():

            self._logger.log(NutsAndBolts.Logger.success, "Entry found, proceeding...")

            # Go through every entry in the project
            for project in indexdata["Projects"]:

                self._logger.log(NutsAndBolts.Logger.info, "Verifying entry : " + str(project))

                if "id" in project.keys() and project["id"] == "default":
                    continue

                # Check the ID
                self._logger.log(NutsAndBolts.Logger.info, "Checking the id field...")
                if "id" not in project.keys():

                    self._logger.log(NutsAndBolts.Logger.error, "There is no entry for ID")
                    success = False

                else:

                    value = project["id"]

                    # Check for duplicate id
                    if value in idlist:
                        self._logger.log(NutsAndBolts.Logger.error, "Id is duplicate")
                        success = False

                    idlist.append(value)

                # Check the app-id
                self._logger.log(NutsAndBolts.Logger.info, "Checking the app-id field")
                if "app-id" not in project.keys():

                    self._logger.log(NutsAndBolts.Logger.error, "Missing app-id entry")
                    success = False

                else:

                    value = project["app-id"]
                    t = value

                # Check job-id
                self._logger.log(NutsAndBolts.Logger.info, "Checking the job-id field")
                if "job-id" not in project.keys():

                    self._logger.log(NutsAndBolts.Logger.error, "Missing job-id entry")
                    success = False

                else:

                    value = project["job-id"]

                    if t is not None:
                        t += "/" + str(value)
                        containerlist.append(t)

                # Check the git url
                self._logger.log(NutsAndBolts.Logger.info, "Checking the git-url field")
                if "git-url" not in project.keys():

                    self._logger.log(NutsAndBolts.Logger.error, "Missing git-url entry")
                    success = False

                # Check git-path
                self._logger.log(NutsAndBolts.Logger.info, "Checking the git-path field")
                if "git-path" not in project.keys():
                    self._logger.log(NutsAndBolts.Logger.error, "Missing git-path entry")
                    success = False

                # Check git branch
                self._logger.log(NutsAndBolts.Logger.info, "Checking the git-branch field")
                if "git-branch" not in project.keys():
                    self._logger.log(NutsAndBolts.Logger.error, "Missing git branch entry")
                    success = False

                # Check notify email
                self._logger.log(NutsAndBolts.Logger.info, "Checking the notify-email field")
                if "notify-email" not in project.keys():
                    self._logger.log(NutsAndBolts.Logger.error, "Missing notify-email entry")
                    success = False

                # Check for target-file entry
                self._logger.log(NutsAndBolts.Logger.info, "Checking for target-file field")
                if "target-file" not in project.keys():
                    self._logger.log(NutsAndBolts.Logger.error, "Missing target-file entry")
                    success = False

                # Check depends on
                self._logger.log(NutsAndBolts.Logger.info, "Checking the depends-on field")
                if "depends-on" not in project.keys():

                    self._logger.log(NutsAndBolts.Logger.error, "Missing depends-on entry")
                    success = False

                else:

                    valuel = project["depends-on"]

                    if valuel is not None:

                        for item in valuel:

                            if item not in containerlist:
                                self._logger.log(NutsAndBolts.Logger.error,
                                                 "Dependency " + item + " missing or not above this item in list")

        else:

            self._logger.log(NutsAndBolts.Logger.error, "Index file doesnt contain Projects entry at top level, failed")
            success = False

        return success

    def run(self):
        """Runs the Index Verifier"""

        self._logger.log(NutsAndBolts.Logger.info, "Preparing the index...")

        # If index can be prepared, only then go ahead with parsing, else failure at this stage itself
        if self._prepareIndex():

            self._logger.log(NutsAndBolts.Logger.info, "Verifying index formatting...")
            return self._verifyIndex()

        else:

            self._logger.log(NutsAndBolts.Logger.error,
                             "Index preperation failed, check the giturl or indexfile specified")

        return False
