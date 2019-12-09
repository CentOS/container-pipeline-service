# scan script for yum list update scanner


from scanners.base_scanner import BaseScanner

import sys
import yum


class SysStdoutSuppressor(object):
    """
    Class which can be used to mute output printed
    on sys.stdout.
    It just mutes the sys.stdout and takes care of raising
    the exception if encountered in calling method.

    Refer <https://www.python.org/dev/peps/pep-0343/> for
    explanation on __enter__ and  __exit__ methods.

    Excerpts from referece:
    Context managers provide __enter__() and __exit__() methods
    that are invoked on entry to and exit from the body of the with statement.
    """

    def __enter__(self):
        """
        This method is executed when the caller method enters in
        the context manager
        """
        self.stdout = sys.stdout
        sys.stdout = self

    def __exit__(self, exc_type, value, traceback):
        """
        This method is executed when the caller method exits from
        the context manager
        """
        # revert back sys.stdout to original form before exiting
        sys.stdout = self.stdout
        if exc_type is not None:
            raise(value)

    def write(self, x):
        """
        Overriding sys.stdout.write method,
        this method won't print on stdout, which is what we want.
        """
        pass


class YumUpdates(BaseScanner):
    """
    This class contains methods to find yum updates and print
    information of RPM updates.
    It uses yum python API client to find the updates.
    """
    NAME = "yum-updates-scanner"
    DESCRIPTION = "Finds yum updates available."

    def __init__(self):
        """
        Instantiate the YumUpdates class and creates
        yum.YumBase class's object
        """
        super(YumUpdates, self).__init__()
        self.yum_obj = yum.YumBase()

    def find_updates(self):
        """
        Find yum updates and returns the updates as list of dictionaries
        with information for package viz: Name, Installed version,
        Update and source yum repo.

        :return: List of dictionaries with info about package updates
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

    def run(self):
        return self.print_updates(self.find_updates())

    def print_updates(self, updates):
        """
        Print the updates on stdout
        :arg updates: Updates provided as list of dictionaries,
                      the output received from find_updates() method
        :type updates: List
        """
        if not updates:
            print("No RPM updates available in the configured yum repos.")
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
