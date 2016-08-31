import os
import urlparse
from glob import glob
from subprocess import check_call, CalledProcessError

import Globals


class Logger:
    """Handles all logging and reporting operations"""
    info = "1"
    success = "2"
    error = "3"

    def __init__(self, logfile=None):

        if logfile is not None:

            if not os.path.exists(logfile):
                with open(logfile, "w"):
                    os.utime(logfile, None)

        self._logFile = logfile

        return

    def log(self, logtype, msg):
        """Logs the message, displaying it on screen, as well as recording it in a file, if one is specified."""

        printmsg = ""
        filemsg = ""

        if logtype == Logger.info:

            printmsg = str.format("\n{0}\t{1}\n", "\033[1;33m[INFO]\033[0m", msg)
            filemsg = str.format("\n{0}\t{1}\n", "INFO", msg)

        elif logtype == Logger.success:

            printmsg = str.format("\n{0}\t{1}\n", "\033[1;32m[OK]\033[0m", msg)
            filemsg = str.format("\n{0}\t{1}\n", "OK", msg)

        elif logtype == Logger.error:

            printmsg = str.format("\n{0}\t{1}\n", "\033[1;31m[ERROR]\033[0m", msg)
            filemsg = str.format("\n{0}\t{1}\n", "ERROR", msg)

        print printmsg

        if self._logFile is not None:
            with open(self._logFile, "a+") as logfile:
                logfile.write(filemsg)

        return


class StaticHandler:

    @staticmethod
    def execcmd(cmd):
        """Executes a cmd list and returns true if cmd executed correctly."""

        success = True

        try:
            check_call(cmd)
            success = True

        except CalledProcessError:
            success = False

        return success

    @staticmethod
    def initialize(data_dump_directory=None, index_git=None, custom_index_location=None, index_git_branch="master"):
        """Initializes some variables, as required, including setting up defaults"""

        Logger().log(Logger.info, "Initializing systems...")

        if data_dump_directory is not None:

            Globals.Globals.setdatadirectory(data_dump_directory)

        else:

            Globals.Globals.setdatadirectory("./cccp-index-test")

        if index_git is not None:
            Globals.Globals.index_git = index_git
            Globals.Globals.index_git_branch = index_git_branch

        if custom_index_location is not None:

            if os.path.exists(custom_index_location):

                Globals.Globals.custom_index_location = custom_index_location

            else:

                Logger().log(Logger.error, "Non existent custom index specified, falling back to index git.")

        Globals.Globals.old_environ = dict(os.environ)

        os.unsetenv("GIT_ASKPASS")
        os.unsetenv("SSH_ASKPASS")

        StaticHandler._setupFS()

        return

    @staticmethod
    def _setupFS():
        """Sets up the filesystem in the dump directory"""

        if not os.path.exists(Globals.Globals.data_dump_directory):
            os.mkdir(Globals.Globals.data_dump_directory)

        if not os.path.exists(Globals.Globals.index_directory):
            os.mkdir(Globals.Globals.index_directory)

        if not os.path.exists(Globals.Globals.repo_directory):
            os.mkdir(Globals.Globals.repo_directory)

        if not os.path.exists(Globals.Globals.tests_directory):
            os.mkdir(Globals.Globals.tests_directory)

        else:

            content = glob(Globals.Globals.tests_directory + "/*")

            for item in content:
                
                os.remove(item)

        return

    @staticmethod
    def cleanup():

        os.environ.update(Globals.Globals.old_environ)

        return

    @staticmethod
    def is_valid_git_url(theurl):
        """Checks if a url is valid format"""

        valid = True

        if theurl is None:
            return False

        parsedurl = urlparse.urlparse(theurl)

        if parsedurl.scheme != "git":
            valid = False

        return valid


class Tracker:
    """Tracker keeps track of information required accross runs"""

    @staticmethod
    def setCustomIndexUsed(used):
        """Sets if a custom indexfile was used"""

        if used:

            with open(Globals.Globals.custom_index_file_indicator, "w"):
                os.utime(Globals.Globals.custom_index_file_indicator, None)

        else:

            if os.path.exists(Globals.Globals.custom_index_file_indicator):
                os.remove(Globals.Globals.custom_index_file_indicator)

        return

    @staticmethod
    def isCustomIndexUsed():
        """Gets if a custom index file was used"""

        used = True

        if not os.path.exists(Globals.Globals.custom_index_file_indicator):
            used = False

        return used

    @staticmethod
    def setPreviousIndexGit(giturl):
        """Sets the previous index giturl"""

        with open(Globals.Globals.previous_index_git_file, "w+") as fl:
            fl.write(giturl)

        return

    @staticmethod
    def getPreviousIndexGit():
        """Gets the previously used index giturl"""

        previous = ""

        if not os.path.exists(Globals.Globals.previous_index_git_file):
            Tracker.setPreviousIndexGit("__NONE__")

        with open(Globals.Globals.previous_index_git_file, "r") as fl:
            previous = fl.readline()

        return previous
