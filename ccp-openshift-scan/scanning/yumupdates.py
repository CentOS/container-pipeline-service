# scan script for yum list update scannr

import lib


def yum_updates():
    """
    Finds yum updates
    """
    command = ["yum", "-q", "check-update"]
    out, err = lib.run_cmd_out_err(command)
    return out, err


def find_updates():
    """
    process yum updates
    """
    out, err = yum_updates()
    if err:
        print ("Error:")
        print ("Error retrieving yum updates.\n{}".format(err))
        return
    out = out.strip()

    if not out:
        print ("No yum updates required.")
        return

    out = out.split("\n")
    print ("RPM\t\t\tNew-Version")
    for update in out:
        # split each line separated by tabs
        update = update.split()
        print ("{}\t\t{}".format(update[0], update[1]))


if __name__ == "__main__":
    find_updates()
