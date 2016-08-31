#!/bin/python

import os
import subprocess
from time import sleep

import yaml

from Globals import Globals
from NutsAndBolts import StaticHandler, Logger


class ValidateEntry:
    """This class runs tests on a single entry"""

    def __init__(self, appid, jobid, giturl, git_path, gitbranch, notifyemail, targetfile):

        if not git_path.startswith("/"):
            git_path = "/" + git_path

        if not git_path.endswith("/"):
            git_path += "/"

        fnm = appid + "_" + jobid
        self._git_repos_location = Globals.repo_directory

        self._test_og_File = Globals.tests_directory + "/" + fnm + ".log"
        self._logger = Logger(self._test_og_File)

        self._app_id = appid
        self._job_id = jobid
        self._git_url = giturl
        self._git_path = git_path
        self._git_branch = gitbranch
        self._notify_email = notifyemail
        self._target_file = targetfile

        t = ""

        # The repos will be cloned into this location
        if ":" in self._git_url:
            t = self._git_url.split(":")[1]
        if t.startswith("//"):
            t = t[2:]

        self._git_clone_location = self._git_repos_location + "/" + t

        # The location in the git repo against which the tests are to be run
        self._cccp_test_dir = self._git_clone_location + self._git_path

        self._test_data = {
            "clone-path": self._git_clone_location,
            "git-path": self._git_path,
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

        with open(self._test_og_File, "a") as infofile:
            infofile.write("\n" + msg + "\n")

        return

    def _init_entries(self):
        """Write the initial entries into this tests log file."""

        info = str.format("APP ID : {0}\nJOB ID : {1}\n", self._app_id, self._job_id)
        print info
        info += "GIT : " + self._git_url + "\n"

        info += "######################################################################################################"
        info += "\n"

        with open(self._test_og_File, "w") as infofile:
            infofile.write(info)

        return

    def _update_branch(self):
        """Fetches any changes and checks out specified branch"""

        currdir = os.getcwd()

        os.chdir(self._git_clone_location)
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
        cmd = ["git", "checkout", "origin/" + self._git_branch]
        subprocess.call(cmd)

        os.chdir(currdir)

        return

    def _clone_repo(self):
        """Function attempts to clone the git repo associated with the entry"""

        success = True

        if os.path.exists(self._git_clone_location):

            self._logger.log(Logger.info, "Git repo already exist, checking for updates...")
            self._update_branch()
            self._logger.log(Logger.success, "Changes if any, have been merged...")

        else:

            self._logger.log(Logger.info, "Attempting to clone repo...")
            cmd = ["git", "clone", self._git_url, self._git_clone_location]

            if StaticHandler.execcmd(cmd):
                self._logger.log(Logger.success, "Cloning successful.")
                self._logger.log(Logger.info, "Checking out branch " + self._git_branch + "...")
                self._update_branch()

            else:

                self._logger.log(Logger.error, "Failed to clone repo, skipping...")
                success = False

        self._test_data["tests"]["clone"] = success
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
                self._test_data["tests"]["cccpexists"] = True
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

            if self._job_id == cccpyaml["job-id"]:

                self._logger.log(Logger.success, "Job id matched, moving on...")
                self._test_data["tests"]["jobidmatch"] = True

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
                self._test_data["tests"]["test-skip"] = True

            else:

                self._logger.log(Logger.error, "Test skip is a flag and should have true or false value, skipping")
                return

        else:

            self._logger.log(Logger.success, "Test skip not found, assuming True and moving on...")
            self._test_data["tests"]["test-skip"] = True

        self._logger.log(Logger.info, "Checking for target file")

        # * Check for target-file
        if self._target_file is not None:

            targetfilepath = self._cccp_test_dir + self._target_file

            if not os.path.exists(targetfilepath):

                self._logger.log(Logger.error, "Target file not found, skipping")
                return

            else:

                self._logger.log(Logger.success, "Target file found, moving on")
                self._test_data["tests"]["target-file"] = True

        # * Check for Test script
        if "test-script" in cccpyaml.keys():

            test_script = cccpyaml["test-script"]
            test_script_path = self._cccp_test_dir + test_script

            if not os.path.exists(test_script_path):

                self._logger.log(Logger.error, "Could not find test script, skipping")
                return

            else:

                self._logger.log(Logger.success, "Test script found, moving on")
                self._test_data["tests"]["test-script"] = True

        else:

            self._logger.log(Logger.success, "No test script specified.")
            self._test_data["tests"]["test-script"] = True

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
                self._test_data["tests"]["build-script"] = True

        else:

            self._logger.log(Logger.success, "No build script specified, moving on")
            self._test_data["tests"]["build-script"] = True

        # * Check Local Delivery

        # * Set the all pass flag
        self._test_data["tests"]["allpass"] = self._test_data["tests"]["cccpexists"] and self._test_data["tests"][
            "clone"] and self._test_data["tests"]["jobidmatch"] and \
                                              (
                                                  self._test_data["tests"]["test-skip"] and
                                                  self._test_data["tests"]["test-script"]
                                             ) and \
                                              self._test_data["tests"]["build-script"] and self._test_data["tests"]["target-file"]

        return

    def run(self):
        """This function runs all the necessary tests and returns the collected test data."""

        self._init_entries()

        if self._clone_repo():
            self._test_cccp_yaml()

        sleep(4)

        return self._test_data
