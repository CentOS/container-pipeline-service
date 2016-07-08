import yaml

from Globals import Globals
from ValidateEntry import ValidateEntry


class IndexEntriesVerifier:
    """Handles the verification of individual index entries, w.r.t index.yml and cccp.yml,
     based on Engines instructions"""

    def __init__(self, specificindexentries=None, testindexentries=None):
        """Initialize the Index entries verifier, telling it if you want any specific entries only to be tested"""

        self._specificIndexEntries = specificindexentries
        self._testIndexEntries = testindexentries

        self._buildLogs = {
            "ProjectLogs": [

            ]
        }

        return

    def _addToFinalLog(self, tid, appid, jobid, resultset):
        """Adds test results to the log file of this guy."""

        self._buildLogs["ProjectLogs"].append(
            {
                "id": tid,
                "app-id": appid,
                "job-id": jobid,
                "results": resultset
            }
        )

        return

    def _writeFinalLog(self):
        """Dumps the gathered logs into the file."""

        with open(Globals.buildinfo, "w+") as buildinfofile:

            yaml.dump(self._buildLogs, buildinfofile)

        return

    def run(self):
        """Runs the verifier, checking invidual entires. The repo is cloned for the purpose fo verifications"""

        success = True
        successlist = []
        indexdata = None

        # Read the index.yml file
        with open(Globals.indexFile) as indexfile:
            indexdata = yaml.load(indexfile)

        # Check if any specificindexentries or testindexentries are specified.
        # If not, we need to run against all index entries
        if self._specificIndexEntries is None and self._testIndexEntries is None:
            for project in indexdata["Projects"]:

                tid = project["id"]
                appid = project["app-id"]
                jobid = project["job-id"]
                giturl = project["git-url"]
                gitbranch = project["git-branch"]
                gitpath = project["git-path"]
                notifyemail = project["notify-email"]

                # Default id indicates template, so no tests are run against it.
                if tid != "default":
                    testresults = ValidateEntry(tid, appid, jobid, giturl, gitpath, gitbranch, notifyemail).run()
                    successlist.append(testresults["tests"]["allpass"])
                    self._addToFinalLog(tid, appid, jobid, testresults)

        else:

            # Check any specific index entries - this happens when user specifies specifiec ids from the index
            if self._specificIndexEntries is not None:

                for project in indexdata["Projects"]:

                    tid = project["id"]

                    if tid in self._specificIndexEntries:

                        appid = project["app-id"]
                        jobid = project["job-id"]
                        giturl = project["git-url"]
                        gitbranch = project["git-branch"]
                        gitpath = project["git-path"]
                        notifyemail = project["notify-email"]

                        if tid != "default":
                            testresults = ValidateEntry(tid, appid, jobid, giturl, gitpath, gitbranch,
                                                        notifyemail).run()
                            successlist.append(testresults["tests"]["allpass"])
                            self._addToFinalLog(tid, appid, jobid, testresults)

            # Check Test index entries, if specified - Test entries are independent of indexentries,
            # but will be indirectly affected
            if self._testIndexEntries is not None:

                for item in self._testIndexEntries:
                    tid = item[0]
                    appid = item[1]
                    jobid = item[2]
                    giturl = item[3]
                    gitpath = item[4]
                    gitbranch = item[5]
                    notifyemail = item[6]

                    testresults = ValidateEntry(tid, appid, jobid, giturl, gitpath, gitbranch, notifyemail).run()
                    successlist.append(testresults["tests"]["allpass"])
                    self._addToFinalLog(tid, appid, jobid, testresults)

        self._writeFinalLog()

        if False in successlist:
            success = False

        return success
