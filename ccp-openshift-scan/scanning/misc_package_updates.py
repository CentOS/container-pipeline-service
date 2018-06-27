#!/usr/bin/env python

# this scan file has utilities to find pip, npm, gem package updates

import lib

import sys


def binary_does_not_exist(response):
    """
    Used to figure if the npm, pip, gem binary exists in the container image
    """
    if 'executable file not found in' in response or \
            'not found' in response or \
            'No such file or directory' in response:
        return True
    return False


def find_pip_updates(executable="/usr/bin/pip"):
    """
    Finds out outdated installed packages of pip
    """
    command = [executable, "list", "--outdated", "--disable-pip-version-check"]
    out, err = [], ""

    try:
        out, err = lib.run_cmd_out_err(command)
    except Exception as e:
        err = e

    if err:
        if binary_does_not_exist(err):
            return "{} is not installed".format(executable)
        else:
            return "Failed to find the pip updates."
    else:
        if out.strip():
            return out.strip().split("\n")
        else:
            return []


def find_npm_updates(executable="/usr/bin/npm"):
    """
    Finds out outdated installed packages of npm
    """
    command = [executable, "-g", "outdated"]
    out, err = [], ""

    try:
        out, err = lib.run_cmd_out_err(command)
    except Exception as e:
        err = e

    if err:
        if binary_does_not_exist(err):
            return "{} is not installed".format(executable)
        else:
            return "Failed to find the npm updates."
    else:
        if out.strip():
            return out.strip().split("\n")
        else:
            return []


def find_gem_updates(executable="/usr/bin/gem"):
    """
    Finds out outdated installed packages of gem
    """
    command = [executable, "outdated"]
    out, err = [], ""

    try:
        out, err = lib.run_cmd_out_err(command)
    except Exception as e:
        err = e

    if err:
        if binary_does_not_exist(err):
            return "{} is not installed".format(executable)
        else:
            return "Failed to find the gem updates."
    else:
        if out.strip():
            return out.strip().split("\n")
        else:
            return []


def print_updates(binary):
    """
    Prints the updates found using givn binary
    """
    print ("\n{} updates scan:".format(binary))

    if binary == "npm":
        result = find_npm_updates()
    elif binary == "gem":
        result = find_gem_updates()
    elif binary == "pip":
        result = find_pip_updates()
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
        print ("Please provide at least one argument as:")
        print ("python misc_package_updates.py npm")
        print ("Valid arguments: {}".format(valid_args))
        sys.exit(1)

    cli_arg = sys.argv[1].strip()

    if cli_arg not in valid_args:
        print ("Please provide valid args among {}".format(valid_args))
        sys.exit(1)

    if cli_arg == "all":
        print_updates("pip")
        print_updates("npm")
        print_updates("gem")
    else:
        print_updates(cli_arg)
