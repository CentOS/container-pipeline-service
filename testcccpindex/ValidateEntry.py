#!/bin/python

import os
import yaml
from time import sleep
from ValidatorGlobals import ValidatorGlobals
from subprocess import call
from StaticHandler import StaticHandler, MessageType


class ValidateEntry:
    """This class runs tests on a single entry"""

    def __init__(self, tid, appid, jobid, giturl, gitpath, gitbranch, notifyemail):

        if not gitpath.startswith("/"):
            gitpath = "/" + gitpath

        if not gitpath.endswith("/"):
            gitpath += "/"

        fnm = str(tid) + "_" + appid + "_" + jobid
        self._gitReposlocation = ValidatorGlobals.testdir + "/repos"

        if not os.path.exists(ValidatorGlobals.testdir + "/tests"):
            os.mkdir(ValidatorGlobals.testdir + "/tests")

        self._testLogFile = ValidatorGlobals.testdir + "/tests/" + fnm + ".log"

        self._id = tid
        self._appId = appid
        self._jobId = jobid
        self._gitURL = giturl
        self._gitPath = gitpath
        self._gitBranch = gitbranch
        self._notifyEmail = notifyemail

        t = ""

        # The repos will be cloned into this location
        t = self._gitURL.split(":")[1]
        if t.startswith("//"):
            t = t[2:]

        self._gitCloneLocation = self._gitReposlocation + "/" + t

        # The location in the git repo against which the tests are to be run
        self._cccp_test_dir = self._gitCloneLocation + self._gitPath

        self._testData = {
            "clone-path": self._gitCloneLocation,
            "git-path": self._gitPath,
            "tests": {
                "clone": False,
                "cccpexists": False,
                "jobidmatch": False,
                "test-skip": False,
                "test-script": False,
                "build-script": False,
                "allpass": False
            }
        }

        return

    def write_info(self, msg):
        """Allows outsiders to write to this Entries test.info file."""

        with open(self._testLogFile, "a") as infofile:
            infofile.write("\n" + msg + "\n")

        return

    def _init_entries(self):
        """Write the initial entries into this tests log file."""

        info = str.format("ID : {0}\nAPP ID : {1}\nJOB ID : {2}\n", self._id, self._appId, self._jobId)
        print info
        info += "GIT : " + self._gitURL + "\n"

        info += "######################################################################################################"
        info += "\n"

        with open(self._testLogFile, "w") as infofile:
            infofile.write(info)

        return

    def _update_branch(self):
        """Fetches any changes and checks out specified branch"""

        currdir = os.getcwd()

        os.chdir(self._gitCloneLocation)

        cmd = ["git", "branch", self._gitBranch]
        call(cmd) or True

        cmd = ["git", "pull", "--all"]
        call(cmd)

        cmd = ["git", "checkout", self._gitBranch]
        call(cmd)

        os.chdir(currdir)

        return

    def _clone_repo(self):
        """Function attempts to clone the git repo associated with the entry"""

        success = True

        if os.path.exists(self._gitCloneLocation):

            StaticHandler.print_msg(MessageType.info, "Git repo already exist, checking for updates...", self)
            self._update_branch()
            StaticHandler.print_msg(MessageType.success, "Changes if any, have been merged...", self)

        else:

            StaticHandler.print_msg(MessageType.info, "Attempting to clone repo...", self)
            cmd = ["git", "clone", self._gitURL, self._gitCloneLocation]

            if StaticHandler.execcmd(cmd):
                StaticHandler.print_msg(MessageType.success, "Cloning successful.")
                StaticHandler.print_msg(MessageType.info, "Checking out branch " + self._gitBranch + "...", self)
                self._update_branch()

            else:

                StaticHandler.print_msg(MessageType.error, "Failed to clone repo, skipping...", self)
                ValidatorGlobals.exitcode += 1
                success = False

        self._testData["tests"]["clone"] = success
        return success

    def _test_cccp_yaml(self):
        """Run sanity checks on the cccp.yml file"""

        # FIXME : Finish this method

        # * Find out the the cccp yml file is present

        # Map location of the cccp.yml file
        cccpyamlfilepath = ""

        StaticHandler.print_msg(MessageType.info, "Checking if a cccp.yml file exists at specified location", self)

        # Check if the cccp.yml file exists
        pthexists = False
        for itm in ["cccp.yml", ".cccp.yml", "cccp.yaml", ".cccp.yaml"]:

            cccpyamlfilepath = self._cccp_test_dir + itm

            if os.path.exists(cccpyamlfilepath):
                pthexists = True
                self._testData["tests"]["cccpexists"] = True
                break

        if not pthexists:
            StaticHandler.print_msg(MessageType.error, "Missing cccp.yml file, skipping...", self)
            return

        StaticHandler.print_msg(MessageType.success, "Found cccp.yml file, moving on...", self)

        # * Validate for job-id

        # Check if the job id supplied matches with job id in cccp.yml
        with open(cccpyamlfilepath) as cccpyamlfile:
            cccpyaml = yaml.load(cccpyamlfile)

        StaticHandler.print_msg(MessageType.info, "Matching job id with one in cccp.yml", self)

        #        print str.format("index jid : {0}\ncccp jid : {1}", self._jobid, cccpyaml["job-id"])

        if "job-id" in cccpyaml.keys():

            if self._jobId == cccpyaml["job-id"]:

                StaticHandler.print_msg(MessageType.success, "Job id matched, moving on...", self)
                self._testData["tests"]["jobidmatch"] = True

            else:

                StaticHandler.print_msg(MessageType.error, "Job Ids don't match, skipping...", self)
                ValidatorGlobals.exitcode += 1
                return

        else:

            StaticHandler.print_msg(MessageType.error, "Missing compulsory key, job-id in cccp.yml file...", self)
            ValidatorGlobals.exitcode += 1
            return

        # * Validate for test-skip and test-script

        StaticHandler.print_msg(MessageType.info, "Checking for test-skip flag", self)

        # Check for test skip to be present
        if "test-skip" in cccpyaml.keys():

            StaticHandler.print_msg(MessageType.info, "Flag found, proceeding to check if its reset...", self)

            # Check is test-skip is reset
            if not cccpyaml["test-skip"]:

                StaticHandler.print_msg(MessageType.info, "Test skip is reset, checking for now compulsory test-script",
                                        self)

                self._testData["tests"]["test-skip"] = True

                # Check if a test-script key is present
                if "test-script" in cccpyaml.keys():

                    testscript = cccpyaml["test-script"]
                    testscriptpath = self._cccp_test_dir + testscript

                    # Check if the test script actually exists
                    if not os.path.exists(testscriptpath):

                        StaticHandler.print_msg(MessageType.error,
                                                "The specified test script does not exist, skipping...", self)

                        ValidatorGlobals.exitcode += 1
                        return

                    else:

                        StaticHandler.print_msg(MessageType.success, "The specified test script exists, moving on...",
                                                self)

                        self._testData["tests"]["test-script"] = True

                else:

                    StaticHandler.print_msg(MessageType.error,
                                            "Test skip is reset, but test script is missing, skipping...", self)
                    ValidatorGlobals.exitcode += 1
                    return

            # If test-skip is not reset, check if its set
            elif cccpyaml["test-skip"]:

                StaticHandler.print_msg(MessageType.success, "Test skip is set, moving on...", self)
                self._testData["tests"]["test-skip"] = True
                self._testData["tests"]["test-script"] = True

            # If test-skip is not reset or set, then, there is an error
            else:

                StaticHandler.print_msg(MessageType.error, "Test skip is not reset or set, skipping...", self)
                ValidatorGlobals.exitcode += 1
                return

        else:

            StaticHandler.print_msg(MessageType.success, "Test skip not found, assuming True and moving on...", self)
            self._testData["tests"]["test-skip"] = True
            self._testData["tests"]["test-script"] = True

        # * Check Build script
        StaticHandler.print_msg(MessageType.info, "Checking for build script.", self)
        if "build-script" in cccpyaml.keys():

            buildscriptfile = cccpyaml["build-script"]
            buildscriptpath = self._cccp_test_dir + buildscriptfile

            if not os.path.exists(buildscriptpath):

                StaticHandler.print_msg(MessageType.error, "Could not find build script, skipping", self)
                ValidatorGlobals.exitcode += 1
                return

            else:
                StaticHandler.print_msg(MessageType.success, "Found specified build script.", self)
                self._testData["tests"]["build-script"] = True

        else:

            StaticHandler.print_msg(MessageType.success, "No build script specified, moving on", self)
            self._testData["tests"]["build-script"] = True

        # * Check Local Delivery

        # * Set the all pass flag
        self._testData["tests"]["allpass"] = self._testData["tests"]["cccpexists"] and self._testData["tests"][
            "clone"] and self._testData["tests"]["jobidmatch"] and \
                                             (
                                                 self._testData["tests"]["test-skip"] and
                                                 self._testData["tests"]["test-script"]
                                             ) and \
                                             self._testData["tests"]["build-script"]

        return

    def run_tests(self):
        """This function runs all the necessary tests and returns the collected test data."""

        self._init_entries()

        if self._clone_repo():
            self._test_cccp_yaml()

        sleep(4)

        return self._testData