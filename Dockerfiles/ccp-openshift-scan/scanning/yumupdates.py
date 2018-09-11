# scan script for yum list update scanner

import sys
import yum


class SysStdoutSuppressor(object):
    """
    Class which can be used to mute output printed
    on sys.stdout.
    It just mutes the sys.stdout and takes care of raising
    the exception if encountered in calling method.
    """

    def __enter__(self):
        self.stdout = sys.stdout
        sys.stdout = self

    def __exit__(self, type, value, traceback):
        # revert back sys.stdout to original form before exiting
        sys.stdout = self.stdout
        if type is not None:
            raise(value)

    def write(self, x):
        """
        Overriding sys.stdout.write, this method won't print
        on stdout
        """
        pass


class YumUpdates(object):
    """
    Class with related methods to find the yum updates
    available using python yum API client
    """

    def __init__(self):
        """
        Instantiate
        :arg needed_fields: Properties of RPM object  while processing
        """
        self.yum_obj = yum.YumBase()
        self.needed_fields = ["name", "vra", "repo"]

    def find_updates(self):
        """
        Find yum updates and returns the needed_fields attributes of RPM
        as dictionary for available RPM updates. Returns empty dictionary
        if no updates are required.

        :return: List of dictionaries of needed_fields as keys and value
                 as its output
        :rtype: List
        """
        # narrow the package filter to updates
        rpms = self.yum_obj.doPackageLists(pkgnarrow="updates")
        updates = []
        for each in rpms:
            # check if generator even returned an object
            # case when no updates are available
            if not each:
                continue

            # this is to find out the installed version of
            # package which is listed in update
            installed_rpm_gen = self.yum_obj.doPackageLists(
                pkgnarrow="installed",
                patterns=[each.name])

            # since it returns a generator, we need to iterate
            installed_rpm = ""
            for i in installed_rpm_gen:
                installed_rpm = i
                break

            updates.append(
                {
                    "name": each.name,
                    "installed": installed_rpm,
                    "update": each.ui_nevra,
                    "repo": each.repo
                }
            )
        return updates

    def print_updates(self, updates):
        """
        Print the updates on stdout
        :arg updates: Updates provided as list of dictionaries,
                      the output received from find_updates() method
        :type updates: List
        """
        if not updates:
            print("No RPM updates available as per configured yum repos.")
            return

        # print the number of updates available
        print ("About {0} RPM updates are identified.".format(len(updates)))

        # now print individual RPM update info
        for each in updates:
            # separate updates with extra new lines
            print("\n")
            print("Name:        {0}".format(each["name"]))
            print("Installed:   {0}".format(each["installed"]))
            print("Update :     {0}".format(each["update"]))
            print("Yum Repo:    {0}".format(each["repo"]))


if __name__ == "__main__":
    y = YumUpdates()
    # prevent repo update downloads stdout
    with SysStdoutSuppressor():
        updates = y.find_updates()
    y.print_updates(updates)
