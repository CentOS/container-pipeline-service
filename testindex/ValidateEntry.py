#!/bin/python

import os
import subprocess
from time import sleep

import yaml

from Globals import Globals
from NutsAndBolts import StaticHandler, Logger


class ValidateEntry:
    """This class runs tests on a single entry"""

    def __init__(self, tid, appid, jobid, giturl, gitpath, gitbranch, notifyemail, targetfile):

        if not gitpath.startswith("/"):
            gitpath = "/" + gitpath

        if not gitpath.endswith("/"):
            gitpath += "/"

        fnm = str(tid) + "_" + appid + "_" + jobid
        self._gitReposlocation = Globals.repoDirectory

        self._testLogFile = Globals.testsDirectory + "/" + fnm + ".log"
        self._logger = Logger(self._testLogFile)

        self._id = tid
        self._appId = appid
        self._jobId = jobid
        self._gitURL = giturl
        self._gitPath = gitpath
        self._gitBranch = gitbranch
        self._notifyEmail = notifyemail
        self._targetfile = targetfile

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
                "target-file": False,
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
        cmd = "git branch -r | grep -v '\->' | while read remote; do git branch --track \"${remote#origin/}\"" \
              " \"$remote\"; done"

        # Get all the branches
        os.system(cmd)

        # fetch the branches
        cmd = ["git", "fetch", "--all"]
        subprocess.call(cmd)

        # Pull for update
        cmd = ["git", "pull", "--all"]
        subprocess.call(cmd)

        # Checkout required branch
        cmd = ["git", "checkout", "origin/" + self._gitBranch]
        subprocess.call(cmd)

        os.chdir(currdir)

        return

    def _clone_repo(self):
        """Function attempts to clone the git repo associated with the entry"""

        success = True

        if os.path.exists(self._gitCloneLocation):

            self._logger.log(Logger.info, "Git repo already exist, checking for updates...")
            self._update_branch()
            self._logger.log(Logger.success, "Changes if any, have been merged...")

        else:

            self._logger.log(Logger.info, "Attempting to clone repo...")
            cmd = ["git", "clone", self._gitURL, self._gitCloneLocation]

            if StaticHandler.execcmd(cmd):
                self._logger.log(Logger.success, "Cloning successful.")
                self._logger.log(Logger.info, "Checking out branch " + self._gitBranch + "...")
                self._update_branch()

            else:

                self._logger.log(Logger.error, "Failed to clone repo, skipping...")
                success = False

        self._testData["tests"]["clone"] = success
        return success

    def _test_cccp_yaml(self):
        """Run sanity checks on the cccp.yml file"""

        # FIXME : Finish this method

        # * Find out the the cccp yml file is present

        # Map location of the cccp.yml file
        cccpyamlfilepath = ""

        self._logger.log(Logger.info, "Checking if a cccp.yml file exists at specified location")

        # Check if the cccp.yml file exists
        pthexists = False
        for itm in ["cccp.yml", ".cccp.yml", "cccp.yaml", ".cccp.yaml"]:

            cccpyamlfilepath = self._cccp_test_dir + itm

            if os.path.exists(cccpyamlfilepath):
                pthexists = True
                self._testData["tests"]["cccpexists"] = True
                break

        if not pthexists:
            self._logger.log(Logger.error, "Missing cccp.yml file, skipping...")
            return

        self._logger.log(Logger.success, "Found cccp.yml file, moving on...")

        # * Validate for job-id

        # Check if the job id supplied matches with job id in cccp.yml
        with open(cccpyamlfilepath) as cccpyamlfile:
            cccpyaml = yaml.load(cccpyamlfile)

        self._logger.log(Logger.info, "Matching job id with one in cccp.yml")

        #        print str.format("index jid : {0}\ncccp jid : {1}", self._jobid, cccpyaml["job-id"])

        if "job-id" in cccpyaml.keys():

            if self._appId == "pipeline-images" or self._jobId == cccpyaml["job-id"]:

                self._logger.log(Logger.success, "Job id matched, moving on...")
                self._testData["tests"]["jobidmatch"] = True

            else:

                self._logger.log(Logger.error, "Job Ids don't match, skipping...")
                return

        else:

            self._logger.log(Logger.error, "Missing compulsory key, job-id in cccp.yml file...")
            return

        # * Validate for test-skip

        self._logger.log(Logger.info, "Checking for test-skip flag")

        # Check for test skip to be present
        if "test-skip" in cccpyaml.keys():

            self._logger.log(Logger.info, "Flag found, proceeding to check if its set or reset...")

            # Check is test-skip is set or reset
            if str(cccpyaml["test-skip"]) == str(True) or str(cccpyaml["test-skip"]) == str("False"):

                self._logger.log(Logger.success, "Test skip is a flag, moving on")
                self._testData["tests"]["test-skip"] = True

            else:

                self._logger.log(Logger.error, "Test skip is a flag and should have true or false value, skipping")
                return

        else:

            self._logger.log(Logger.success, "Test skip not found, assuming True and moving on...")
            self._testData["tests"]["test-skip"] = True

        self._logger.log(Logger.info, "Checking for target file")

        # * Check for target-file
        if self._targetfile is not None:

            targetfilepath = self._cccp_test_dir + self._targetfile

            if not os.path.exists(targetfilepath):

                self._logger.log(Logger.error, "Target file not found, skipping")
                return

            else:

                self._logger.log(Logger.success, "Target file found, moving on")
                self._testData["tests"]["target-file"] = True

        # * Check for Test script
        if "test-script" in cccpyaml.keys():

            testscript = cccpyaml["test-script"]
            testscriptpath = self._cccp_test_dir + testscript

            if not os.path.exists(testscriptpath):

                self._logger.log(Logger.error, "Could not find test script, skipping")
                return

            else:

                self._logger.log(Logger.success, "Test script found, moving on")
                self._testData["tests"]["test-script"] = True

        else:

            self._logger.log(Logger.success, "No test script specified.")
            self._testData["tests"]["test-script"] = True

        # * Check Build script
        self._logger.log(Logger.info, "Checking for build script.")
        if "build-script" in cccpyaml.keys():

            buildscriptfile = cccpyaml["build-script"]
            buildscriptpath = self._cccp_test_dir + buildscriptfile

            if not os.path.exists(buildscriptpath):

                self._logger.log(Logger.error, "Could not find build script, skipping")
                return

            else:
                self._logger.log(Logger.success, "Found specified build script.")
                self._testData["tests"]["build-script"] = True

        else:

            self._logger.log(Logger.success, "No build script specified, moving on")
            self._testData["tests"]["build-script"] = True

        # * Check Local Delivery

        # * Set the all pass flag
        self._testData["tests"]["allpass"] = self._testData["tests"]["cccpexists"] and self._testData["tests"][
            "clone"] and self._testData["tests"]["jobidmatch"] and \
                                             (
                                                 self._testData["tests"]["test-skip"] and
                                                 self._testData["tests"]["test-script"]
                                             ) and \
                                             self._testData["tests"]["build-script"] and self._testData["tests"]["target-file"]

        return

    def run(self):
        """This function runs all the necessary tests and returns the collected test data."""

        self._init_entries()

        if self._clone_repo():
            self._test_cccp_yaml()

        sleep(4)

        return self._testData
