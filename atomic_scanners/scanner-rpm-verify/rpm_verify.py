import json
import os
import re
import sys

from datetime import datetime
from subprocess import Popen, PIPE


# variables based on the `atomic scan` defaults
INDIR = "/scanin"
OUTDIR = "/scanout"


class RPMVerify(object):
    """
    Verify installed RPMs
    """

    def __init__(self, container):
        """
        Initialize variables with in and out mount locations
        """
        self.in_path = os.path.join(INDIR, container)
        self.out_path = os.path.join(OUTDIR, container)
        self.container = container
        self.scan_type = "RPM Verify scan for finding tampered files."
        self.scanner = "scanner-rpm-verify"

        self.result_filename = os.path.join(
            self.out_path,
            self.__class__.__name__ + ".json")

        # json data for the output
        self.json_out = self.template_json_data(
            self.scan_type,
            self.container[1:],
            self.scanner
        )

    def template_json_data(self, scan_type, uuid, scanner):
        current_time = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
        json_out = {
            "Start Time": current_time,
            "Successful": "true",
            "Scan Type": scan_type,
            "UUID": uuid,
            "CVE Feed Last Updated": "NA",
            "Scanner": scanner,
            "Scan Results": {}
        }
        return json_out

    def get_command(self):
        """
        Command to run the rpm verify test
        """
        return ["/bin/rpm", "--root=%s" % self.in_path, "-Va"]

    def run_command(self, cmd):
        """
        Run command for rpm verify test
        """
        out, error = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
        return (out, error)

    def get_meta_of_rpm(self, rpm):
        """
        Get metadata of given installed package.
        Metadata captured: SIGPGP, VENDOR, PACKAGER, BUILDHOST
        """
        qf = "%{SIGPGP:pgpsig}|%{VENDOR}|%{PACKAGER}|%{BUILDHOST}"
        cmd = ["/bin/rpm", "--root=%s" % self.in_path, "-q", "--qf", qf, rpm]
        out, _ = self.run_command(cmd)
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
        cmd = ["/bin/rpm", "--root=%s" % self.in_path, "-qf", filepath]
        out, _ = self.run_command(cmd)
        if " " in out:
            return ""
        else:
            return out.split("\n")[0]

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
            match = re.search(r'^([0-9A-Za-z.]+)\s+([c]{0,1})\s+(\W.*)$', line)

            # filter the lines with warnings or errors
            if not match:
                continue

            # filter the config files
            if match.groups()[1] == 'c':
                continue

            filepath = match.groups()[2]
            rpm = self.source_rpm_of_file(filepath)
            rpm_meta = self.get_meta_of_rpm(rpm)
            # do not include the config files in the result

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
        cmd = self.get_command()
        out, error = self.run_command(cmd)
        result = []
        result = self.process_cmd_output_data(out)
        # TODO: since this script is running inside container while we have the
        # logging on host, we should find a better way to log this message back
        # Also we should log the RPMs failing the rpm -V test
        # print "Issue found while running rpm -Va test: "
        # print error
        return {"rpmVa_issues": result}

    def export_results(self, data):
        """
        Export the JSON data in output_file
        """
        os.makedirs(self.out_path)
        current_time = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
        self.json_out["Finished Time"] = current_time
        self.json_out["Scan Results"] = data
        with open(self.result_filename, "w") as f:
            f.write(json.dumps(self.json_out, indent=4))


class Scanner(object):
    """
    Wrapper class for running the scan over images and/or containers
    """

    def target_containers(self):
        """
        Returns the containers / images to be processed
        """
        # atomic scan will mount container's image onto a rootfs and expose rootfs to
        # scanner under the /scanin directory
        return [_dir for _dir in os.listdir(INDIR) if
                os.path.isdir(os.path.join(INDIR, _dir))
                ]

    def format_data(self, data):
        # TBD
        return data

    def run(self):
        for container in self.target_containers():
            # First the image scan

            # Initiate image scan object
            scanner_obj = RPMVerify(container)

            # Run the scanner for given container
            data = scanner_obj.run()

            # Write scan results to json file
            scanner_obj.export_results(self.format_data(data))


if __name__ == "__main__":
    scanner = Scanner()
    scanner.run()
