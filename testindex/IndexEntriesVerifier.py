import yaml

from Globals import Globals
from ValidateEntry import ValidateEntry
from glob import glob
import os


class IndexEntriesVerifier:
    """Handles the verification of individual index entries, w.r.t index.yml and cccp.yml,
     based on Engines instructions"""

    def __init__(self):
        """Initialize the Index entries verifier, telling it if you want any specific entries only to be tested"""

        self._buildLogs = {
            "ProjectLogs": [

            ]
        }

        return

    def _addToFinalLog(self, appid, jobid, resultset):
        """Adds test results to the log file of this guy."""

        self._buildLogs["ProjectLogs"].append(
            {
                "app-id": appid,
                "job-id": jobid,
                "results": resultset
            }
        )

        return

    def _writeFinalLog(self):
        """Dumps the gathered logs into the file."""

        with open(Globals.build_info, "w+") as buildinfofile:

            yaml.dump(self._buildLogs, buildinfofile)

        return

    def run(self):
        """Runs the verifier, checking invidual entires. The repo is cloned for the purpose fo verifications"""

        success = True
        successlist = []
        indexdata = None

        # Check if any specificindexentries or testindexentries are specified.
        # If not, we need to run against all index entries

        for ymlfile in glob(Globals.index_location + "/*.yml"):

            ymldata = ""
            file_name = os.path.split(ymlfile)[1]

            if file_name != "index_template.yml" and file_name != "container-pipeline.yml":

                with open(ymlfile, "r") as ymldatasource:

                    ymldata = yaml.load(ymldatasource)

                for entry in ymldata:

                    appid = file_name.split(".")[0]
                    rs = ValidateEntry(appid, entry["job-id"], entry["git-url"], entry["git-path"], entry["git-branch"],
                                       entry["notify-email"], entry["target-file"]).run()
                    successlist.append(rs["tests"]["allpass"])
                    self._addToFinalLog(appid, entry["job-id"], rs)

        self._writeFinalLog()

        if False in successlist:
            success = False

        return success
