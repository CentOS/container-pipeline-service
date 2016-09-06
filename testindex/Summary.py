import hashlib
from yaml import dump
from NutsAndBolts import GlobalEnvironment


class Summary:
    """This class summarizes the tests"""

    _summary = {}

    def __init__(self):
        pass

    @staticmethod
    def _get_entry_hash(file_name, entry):

        return hashlib.sha256(file_name + str(entry)).hexdigest()

    @staticmethod
    def get_summary_collector(file_name, entry):

        if file_name not in Summary._summary:
            Summary._summary[file_name] = {}

        entry_hash = Summary._get_entry_hash(file_name, entry)

        if entry_hash not in Summary._summary[file_name]:
            Summary._summary[file_name][entry_hash] = {
                "entry": str(entry),
                "errors": []
            }

        return Summary._summary[file_name][entry_hash]

    @staticmethod
    def print_summary():

        print "\n####################### SUMMARY ##################\n"

        for file_name, entries in Summary._summary.iteritems():
            print " * File Name : " + file_name + "\n"

            for entry_id, entry_info in entries.iteritems():
                print "  ** Entry ID : " + entry_id
                print "  ** Entry    : " + entry_info["entry"]
                valid = True
                valid_str = "\033[1;32mOK\033[0m"
                if len(entry_info["errors"]) > 0:
                    valid = False
                    valid_str = "\033[1;31mNO\033[0m"

                print "  ** Valid    : " + valid_str

                if not valid:
                    for err in entry_info["errors"]:
                        print "  **E " + err

                print "\n"

            with open(GlobalEnvironment.environment.data_dump_directory + "/" + "summary.log", "w") as summary_file:
                dump(Summary._summary, summary_file, default_flow_style=False)
