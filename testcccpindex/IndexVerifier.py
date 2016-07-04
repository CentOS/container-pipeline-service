import os
import shutil

import yaml

import Globals
import NutsAndBolts


class IndexVerifier:
    def __init__(self):

        self._logger = NutsAndBolts.Logger(Globals.Globals.dataDumpDirectory + "/index.log")

        return

    def _cleanupIndex(self):

        shutil.rmtree(Globals.Globals.indexDirectory)
        os.mkdir(Globals.Globals.indexDirectory)

        return

    def _prepareIndex(self):

        success = True

        # Check if custom index file is specified.
        if Globals.Globals.customIndexFile is not None:

            self._cleanupIndex()
            NutsAndBolts.Tracker.setCustomIndexUsed(True)
            shutil.copy2(Globals.Globals.customIndexFile, Globals.Globals.indexFile)

        # Go to the clone index repo way of doing things
        else:

            # print NutsAndBolts.Tracker.getPreviousIndexGit()

            if NutsAndBolts.Tracker.isCustomIndexUsed() or Globals.Globals.indexGit != NutsAndBolts.Tracker.getPreviousIndexGit():

                self._cleanupIndex()

                cmd = ["git", "clone", Globals.Globals.indexGit, Globals.Globals.indexDirectory]
                NutsAndBolts.Tracker.setPreviousIndexGit(Globals.Globals.indexGit)

                if not NutsAndBolts.StaticHandler.execcmd(cmd):
                    return False

            getback = os.getcwd()
            os.chdir(Globals.Globals.indexDirectory)
            cmd = ["git", "pull", "--all"]
            success = NutsAndBolts.StaticHandler.execcmd(cmd)
            os.chdir(getback)

        return success

    def _verifyIndex(self):

        success = True

        t = None
        idlist = []
        containerlist = []

        # Load the index data
        indexdata = ""

        with open(Globals.Globals.indexFile) as indexfile:
            indexdata = yaml.load(indexfile)

        # Check if projects entry exists
        self._logger.log(NutsAndBolts.Logger.info, "Checking if \"Projects\" entry exists...")

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

                else:

                    value = project["git-url"]

                    if not NutsAndBolts.StaticHandler.is_valid_git_url(value):
                        self._logger.log(NutsAndBolts.Logger.error, "Invalid git url format specified")

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

        self._logger.log(NutsAndBolts.Logger.info, "Preparing the index...")

        if self._prepareIndex():

            self._logger.log(NutsAndBolts.Logger.info, "Verifying index formatting...")
            return self._verifyIndex()

        else:

            self._logger.log(NutsAndBolts.Logger.error,
                             "Index preperation failed, check the giturl or indexfile specified")

        return False
