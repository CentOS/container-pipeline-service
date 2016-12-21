import hashlib
from datetime import datetime

from yaml import dump


class SummaryCollector(object):
    """This class hides away the problem of errors updating information to summary"""

    def __init__(self, context, file_name, entry):
        self._context = context
        self._summary_info = self._context.summary.get_summary_object(file_name, entry)

    def add_error(self, msg):
        self._summary_info["errors"].append(msg)

    def add_warning(self, msg):
        self._summary_info["warnings"].append(msg)


class Summary(object):
    """This class summarizes the tests"""

    def __init__(self, summary_dump):
        self.global_errors = []
        self._summary = {}
        self._summary_dump = summary_dump
        pass

    @staticmethod
    def _get_entry_hash(file_name, entry):

        return hashlib.sha256(file_name + str(entry)).hexdigest()

    def get_summary_object(self, file_name, entry):

        if file_name not in self._summary:
            self._summary[file_name] = {}

        entry_hash = Summary._get_entry_hash(file_name, entry)

        if entry_hash not in self._summary[file_name]:
            self._summary[file_name][entry_hash] = {
                "entry": str(entry),
                "errors": [],
                "warnings": []
            }

        return self._summary[file_name][entry_hash]

    def print_summary(self):

        print "\n####################### SUMMARY ##################\n"

        print "\nGLOBAL ERRORS:\n"
        if len(self.global_errors) == 0:
            print "NONE\n"
        else:
            for err in self.global_errors:
                print "**E " + err
            print

        for file_name, entries in self._summary.iteritems():
            print " * File Name : " + file_name + "\n"

            for entry_id, entry_info in entries.iteritems():
                print "  ** Entry ID : " + entry_id
                print "  ** Entry    : " + entry_info["entry"]
                valid = True
                valid_str = "\033[1;32mOK\033[0m"
                if len(entry_info["warnings"]) > 0:
                    valid_str = "\033[1;33mWARNING\033[0m"
                if len(entry_info["errors"]) > 0:
                    valid = False
                    valid_str = "\033[1;31mNO\033[0m"

                print "  ** Valid    : " + valid_str

                if not valid:
                    for err in entry_info["errors"]:
                        print "  **E " + err

                if len(entry_info["warnings"]) > 0:
                    for wrn in entry_info["warnings"]:
                        print "  **W " + wrn

                print "\n"

            with open(self._summary_dump, "w") \
                    as summary_file:
                dump(self._summary, summary_file, default_flow_style=False)
