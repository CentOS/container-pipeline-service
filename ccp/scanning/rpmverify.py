#!/usr/bin/env python

# rpm verify utility script for verifying installed RPMs in given env
# the script has needed functions to to run `rpm -Va` in given environment
# and filter out config etc files and report the files with issues along
# with meta like RPM name etc


import re
import sys

from scanners.base_scanner import BaseScanner, BinaryDoesNotExist


class RPMVerify(BaseScanner):
    """
    Verify installed RPMs
    """
    NAME = "rpm-verify-scanner"
    DESCRIPTION = 'Verify installed RPMs and report issues if any.'
    # Filter the paths you know the resulting image or base image itself
    # has issue about and need to be filtered
    # out since this is a known issue and it is in progress to get fixed.
    FILTER_PATHS = [
        "/",   # centos base image has issue with following files
        "/usr/lib/udev/hwdb.d/20-OUI.hwdb",
        "/usr/lib/udev/hwdb.d/20-acpi-vendor.hwdb",
        "/usr/lib/udev/hwdb.d/20-bluetooth-vendor-product.hwdb",
        "/usr/lib/udev/hwdb.d/20-net-ifname.hwdb",
        "/usr/lib/udev/hwdb.d/20-pci-classes.hwdb",
        "/usr/lib/udev/hwdb.d/20-pci-vendor-model.hwdb",
        "/usr/lib/udev/hwdb.d/20-sdio-classes.hwdb",
        "/usr/lib/udev/hwdb.d/20-sdio-vendor-model.hwdb",
        "/usr/lib/udev/hwdb.d/20-usb-classes.hwdb",
        "/usr/lib/udev/hwdb.d/20-usb-vendor-model.hwdb",
        "/usr/lib/udev/hwdb.d/60-keyboard.hwdb",
        "/usr/lib/udev/hwdb.d/70-mouse.hwdb",
        "/usr/lib/udev/hwdb.d/70-touchpad.hwdb",
        "/usr/lib/udev/hwdb.d/60-evdev.hwdb",
    ]

    # Filter filepaths starting with following directories listing,
    # since these paths are expected to be modified and should not
    # take into account

    FILTER_DIRS = [
        "/var", "/run", "/media", "/mnt", "/tmp", "/proc", "/sys", "/boot"
    ]

    file_issues_semantics = {
        "S": "file Size differs",
        "M": "Mode differs (includes permissions and file type)",
        "5": "digest (formerly MD5 sum) differs",
        "D": "Device major/minor number mismatch",
        "L": "readLink(2) path mismatch",
        "U": "User ownership differs",
        "G": "Group ownership differs",
        "T": "mTime differs",
        "P": "caPabilities differ",
    }

    def __init__(self):
        super(RPMVerify, self).__init__()
        # figure out the absolute path of binary in target system
        self.rpm_binary = self.which("rpm")

    def get_rpm_verify_command(self):
        """
        Command to run the rpm verify test
        """
        return [self.rpm_binary, "-Va"]

    def get_meta_of_rpm(self, rpm):
        """
        Get metadata of given installed package.
        Metadata captured: SIGPGP, VENDOR, PACKAGER, BUILDHOST
        """
        qf = "%{SIGPGP:pgpsig}|%{VENDOR}|%{PACKAGER}|%{BUILDHOST}"
        cmd = ["/bin/rpm", "-q", "--qf", qf, rpm]
        out, _ = self.run_cmd_out_err(cmd)
        out = out.split("|")
        return {"RPM": rpm,
                "SIGNATURE": out[0],
                "VENDOR": out[1],
                "PACKAGER": out[2],
                "BUILDHOST": out[3]
                }

    def source_rpm_of_file(self, filepath):
        """
        Find source RPM of given filepath
        """
        cmd = ["/bin/rpm", "-qf", filepath]
        out, _ = self.run_cmd_out_err(cmd)
        return out.split("\n")[0].strip()

    def filter_expected_dirs_modifications(self, filepath):
        """
        This method filters the expected modifications to directories like
        /var,/run,/media,/mnt,/tmp
        """

        return filepath.startswith(tuple(self.FILTER_DIRS))

    def filter_paths_with_known_issues(self, filepath):
        """
        this method filters the paths which should be filtered from the result
        of scanner since the paths are issues in base image or resulting image
        which are being fixed.
        """

        return filepath in self.FILTER_PATHS

    def process_cmd_output_data(self, data):
        """
        Process the command output data
        """
        lines = data.split("\n")[:-1]
        result = []
        for line in lines:
            line = line.strip()
            if line.startswith("error:"):
                continue

            # matches lines of output which corresponds rpm verify results
            match = re.search(r'^([0-9A-Za-z.]+)\s+([c]{0,1})\s+(\W.*)$', line)

            # filter the lines with warnings or errors
            if not match:
                continue

            # do not include the config files in the result
            # filter the config files
            if match.groups()[1] == 'c':
                continue

            # filter the documentation files
            if match.groups()[1] == 'd':
                continue

            filepath = match.groups()[2].strip()

            # filter the expected directories
            if self.filter_expected_dirs_modifications(filepath):
                continue

            # filter known paths having issues in base image or resulting image
            if self.filter_paths_with_known_issues(filepath):
                continue

            rpm = self.source_rpm_of_file(filepath)

            if not rpm:
                continue

            result.append({
                "issue": match.groups()[0],
                "config": match.groups()[1] == 'c',
                "filename": match.groups()[2],
                "rpm": self.get_meta_of_rpm(rpm)})
        return result

    def run(self):
        """
        Run the RPM verify test
        """
        result = self.output_format.copy()
        result['start_time'] = self.time_now()
        cmd = self.get_rpm_verify_command()
        out, err = self.run_cmd_out_err(cmd)
        result['logs'] = self.process_cmd_output_data(out)
        result['successful'] = True
        result['alert'] = True
        result['end_time'] = self.time_now()
        result['os'] = self.linux_distribution()
        return result

    def print_result(self, result):
        """
        Prints the result
        """
        print ("Scan for verifying installed RPMs:")

        if not result:
            print ("All the RPM installed libraries and "
                   "binaries are intact in image.")
            return
        for line in result:
            print ("\nFile: {0}".format(line.get("filename")))

            # find out what all issues with file are
            file_issues_encoded = line["issue"].strip().replace(".", "")

            # handle the case of missing file separately
            if file_issues_encoded == "missing":
                file_issues = ["The file is missing."]
            else:
                file_issues = [self.file_issues_semantics.get(each, each)
                               for each in file_issues_encoded]

            print ("Issue with file:")
            for issue in file_issues:
                print ("\t- {0}".format(issue))

            print ("RPM info:")
            for key, value in line.get("rpm", {}).iteritems():
                print ("\t{0: <10}: {1}".format(key, value))


if __name__ == "__main__":
    try:
        rpmverify = RPMVerify()
        result = rpmverify.run()
        rpmverify.print_result(result)
    except BinaryDoesNotExist as e:
        print (e)
        print ("Scan is aborted!")
        sys.exit(1)
    except Exception as e:
        print ("Error occurred in RPM Verify scanner execution.")
        print ("Error: {0}".format(e))
        sys.exit(1)
