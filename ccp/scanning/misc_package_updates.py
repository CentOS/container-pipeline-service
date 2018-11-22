#!/usr/bin/env python

# this scan file has utilities to find pip, npm, gem package updates


import sys

from scanners.base_scanner import BaseScanner, BinaryDoesNotExist


class MiscPackageUpdates(BaseScanner):
    """
    Misc package updates scanner
    """
    NAME = "Misc-package-updates"
    DESCRIPTION = "Find updates available for pip, npm, and gem."

    def __init__(self):
        super(MiscPackageUpdates, self).__init__()

    def find_pip_updates(self, binary="pip"):
        """
        Finds out outdated installed packages of pip
        """
        # figure out the absolute path of binary in target system
        binary = self.which(binary)
        command = [binary, "list", "--outdated", "--disable-pip-version-check"]
        out, err = [], ""

        try:
            out, err = self.run_cmd_out_err(command)
        except Exception as e:
            err = e

        if err:
            return "Failed to find the pip updates."
        else:
            if out.strip():
                return out.strip().split("\n")
            else:
                return []

    def find_npm_updates(self, binary="npm"):
        """
        Finds out outdated installed packages of npm
        """
        # figure out the absolute path of binary in target system
        binary = self.which(binary)
        command = [binary, "-g", "outdated"]
        out, err = [], ""

        try:
            out, err = self.run_cmd_out_err(command)
        except Exception as e:
            err = e

        if err:
            return "Failed to find the npm updates."
        else:
            if out.strip():
                return out.strip().split("\n")
            else:
                return []

    def find_gem_updates(self, binary="gem"):
        """
        Finds out outdated installed packages of gem
        """
        # figure out the absolute path of binary in target system
        binary = self.which(binary)
        command = [binary, "outdated"]
        out, err = [], ""

        try:
            out, err = self.run_cmd_out_err(command)
        except Exception as e:
            err = e

        if err:
            return "Failed to find the gem updates."
        else:
            if out.strip():
                return out.strip().split("\n")
            else:
                return []

    def print_updates(self, binary):
        """
        Prints the updates found using given binary
        """
        print ("\n{0} updates scan:".format(binary))

        if binary == "npm":
            result = self.find_npm_updates()
        elif binary == "gem":
            result = self.find_gem_updates()
        elif binary == "pip":
            result = self.find_pip_updates()
        else:
            return

        if result:
            # prints errors
            if isinstance(result, str):
                print (result)
                return
            # prints result
            for line in result:
                print (line)
        else:
            print ("No updates required.")


if __name__ == "__main__":
    valid_args = ["pip", "gem", "npm", "all"]

    if len(sys.argv) < 2:
        example = "python misc_package_updates.py npm"
        print ("Please provide at least one argument as\n{0}".format(example))
        print ("Valid arguments: {0}".format(valid_args))
        sys.exit(1)

    cli_arg = sys.argv[1].strip()

    if cli_arg not in valid_args:
        print ("Please provide valid args among {0}".format(valid_args))
        sys.exit(1)

    try:
        misc_pkg_updates = MiscPackageUpdates('')
        if cli_arg == "all":
            misc_pkg_updates.print_updates("pip")
            misc_pkg_updates.print_updates("npm")
            misc_pkg_updates.print_updates("gem")
        else:
            misc_pkg_updates.print_updates(cli_arg)
    except BinaryDoesNotExist as e:
        print (e)
        print ("Scan is aborted!")
        sys.exit(1)
    except Exception as e:
        print ("Error occurred in Misc Package Updates scanner execution.")
        print ("Error: {0}".format(e))
        sys.exit(1)
