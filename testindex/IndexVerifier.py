import os
import shutil

import yaml

import Globals
import NutsAndBolts

from glob import glob


class IndexVerifier:
    """This is the first pass of the system, validating the formatting of the index file."""

    def __init__(self):
        """Initialize the verifier"""

        self._logger = NutsAndBolts.Logger(Globals.Globals.data_dump_directory + "/index.log")

        return

    def _cleanup_index(self):
        """Cleans up previous index data"""

        shutil.rmtree(Globals.Globals.index_directory)
        os.mkdir(Globals.Globals.index_directory)

        return

    def _prepare_index(self):
        """Prepare the index, by cloning it or copying local index.yml, if specified"""

        success = True

        # Check if custom index file is specified.
        if Globals.Globals.custom_index_location is not None:

            # Clean up previous index
            self._cleanup_index()

            # Tell the tracker what was just done
            NutsAndBolts.Tracker.setCustomIndexUsed(True)

            # Copy over specified index to where it should be
            shutil.copy2(Globals.Globals.custom_index_location, Globals.Globals.index_location)

        # Go to the clone index repo way of doing things
        else:

            # print NutsAndBolts.Tracker.getPreviousIndexGit()

            # If custom indexfile is used, or the tracker says current indexgit is not the same as previous one
            if NutsAndBolts.Tracker.isCustomIndexUsed() or \
                            Globals.Globals.index_git != NutsAndBolts.Tracker.getPreviousIndexGit():

                # Clean up previous.
                self._cleanup_index()

                # Clone the new index
                cmd = ["git", "clone", Globals.Globals.index_git, Globals.Globals.index_directory]
                NutsAndBolts.Tracker.setPreviousIndexGit(Globals.Globals.index_git)

                if not NutsAndBolts.StaticHandler.execcmd(cmd):
                    return False

            getback = os.getcwd()
            os.chdir(Globals.Globals.index_directory)
            cmd = ["git", "fetch", "--all"]
            NutsAndBolts.StaticHandler.execcmd(cmd)
            checkoutbranch = "origin/" + Globals.Globals.index_git_branch
            cmd = ["git", "checkout", checkoutbranch]
            success = NutsAndBolts.StaticHandler.execcmd(cmd)
            cmd = ["git", "pull", "--all"]
            NutsAndBolts.StaticHandler.execcmd(cmd)
            os.chdir(getback)

        return success

    def _verify_index(self):
        """Does the validation of the index.yml formatting"""

        success = True

        t = None
        containerlist = []

        # Load the index data
        indexdata = ""

        self._logger.log(NutsAndBolts.Logger.info, "Checking the index.d files for format errors.")

        for ymlfile in glob(Globals.Globals.index_location + "/*.yml"):

            ymldata = ""
            file_name = os.path.split(ymlfile)[1]

            if file_name != "index_template.yml":

                with open(ymlfile, "r") as ymldatasource:

                    ymldata = yaml.load(ymldatasource)

                for entry in ymldata:

                    # Check for job-id
                    self._logger.log(NutsAndBolts.Logger.info, "Checking for job id")
                    if "job-id" not in entry:

                        self._logger.log(NutsAndBolts.Logger.error, "Missing job-id field.")
                        success = False

                    else:

                        self._logger.log(NutsAndBolts.Logger.success, "Job-id has been specified.")
                        containerlist.append(file_name + "/" + entry["job-id"])

                    # Check git-url
                    self._logger.log(NutsAndBolts.Logger.info, "Checking for git url")
                    if "git-url" not in entry:

                        self._logger.log(NutsAndBolts.Logger.error, "Missing git-url field")
                        success = False

                    else:

                        self._logger.log(NutsAndBolts.Logger.success, "Git url has been specified.")

                    # Check git-path
                    self._logger.log(NutsAndBolts.Logger.info, "Checking for git path")
                    if "git-path" not in entry:

                        self._logger.log(NutsAndBolts.Logger.error, "Git path has not been specified")
                        success = False

                    else:

                        self._logger.log(NutsAndBolts.Logger.success, "Git path has been specified")

                    # Check git-branch
                    self._logger.log(NutsAndBolts.Logger.info, "Checking git branch")
                    if "git-branch" not in entry:

                        self._logger.log(NutsAndBolts.Logger.error, "Git branch has not been specified")
                        success = False

                    else:

                        self._logger.log(NutsAndBolts.Logger.success, "Git branch has been specified.")

                    # Check notify email
                    self._logger.log(NutsAndBolts.Logger.info, "Checking notify email")
                    if "notify-email" not in entry:

                        self._logger.log(NutsAndBolts.Logger.error, "Notify email has not been specified.")
                        success = False

                    else:

                        self._logger.log(NutsAndBolts.Logger.success, "Notify email has been specified.")

            return success

    def run(self):
        """Runs the Index Verifier"""

        self._logger.log(NutsAndBolts.Logger.info, "Preparing the index...")

        # If index can be prepared, only then go ahead with parsing, else failure at this stage itself
        if self._prepare_index():

            self._logger.log(NutsAndBolts.Logger.info, "Verifying index formatting...")
            return self._verify_index()

        else:

            self._logger.log(NutsAndBolts.Logger.error,
                             "Index preperation failed, check the giturl or indexfile specified")

        return False
