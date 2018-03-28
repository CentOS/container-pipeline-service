#!/usr/bin/python

import json
import logging
import os
import sys
import subprocess

from datetime import datetime

# variables based on the `atomic scan` defaults
INDIR = "/scanin"
OUTDIR = "/scanout"

# set up logging
logger = logging.getLogger("container-pipeline")
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
ch.setFormatter(formatter)
logger.addHandler(ch)

# atomic scan will mount container's image onto a rootfs and expose rootfs to
# scanner under the /scanin directory
dirs = [_dir for _dir in os.listdir(INDIR) if
        os.path.isdir(os.path.join(INDIR, _dir))]


def template_json_data(scan_type, uuid, scanner):
    current_time = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
    json_out = {
        "Start Time": current_time,
        "Successful": False,
        "Scan Type": scan_type,
        "UUID": uuid[1:],
        "CVE Feed Last Updated": "NA",
        "Scanner": scanner,
        "Scan Results": {},
        "Summary": ""
    }
    return json_out


class ScanImageRootfs(object):
    """Scan an image provided using the path to its rootfs. ScanImageRootfs
    doesn't spin up a container from the image. All tests are passive.
    """

    def __init__(self, path):
        self.in_path = os.path.join(INDIR, path)
        self.out_path = os.path.join(OUTDIR, path)
        self.image = path
        self.pretty_name = None

        # output file for the scan results
        op_file = "image_scan_results.json"
        self.op_file = os.path.join(self.out_path, op_file)

        # json data for the output
        self.json_out = template_json_data(
            scan_type="Image Scan",
            uuid=self.image,
            scanner="pipeline-scanner"
        )

    def scan_release(self):
        env_vars_dict = dict()
        etc_os_release = os.path.join(self.in_path, "etc/os-release")

        # check if at all /etc/os-release exist even before opening it
        if not os.path.isfile(etc_os_release):
            self.json_out["Scan Results"]["OS Release"] = \
                "Could not find OS release of image under test " \
                "as /etc/os-release file does not exist."
            return

        with open(etc_os_release) as f:
            env_vars = f.readlines()

        for var in env_vars:
            var = var.strip()
            split_var = var.split("=")
            if split_var[0] != "":
                env_vars_dict[split_var[0]] = split_var[1][1:-1]

        self.json_out["Scan Results"]["OS Release"] = \
            env_vars_dict["PRETTY_NAME"]

    def scan_yum_update(self):
        # check update by switching to image's rootfs
        process = subprocess.Popen([
            'yum', '-q', 'check-update', '--installroot=%s' % self.in_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        resp, err = process.communicate()

        # initialize the response as list
        updates = []

        if resp != "":
            self.json_out["Summary"] = "RPM updates available for the image."
            self.json_out["Successful"] = True
            updates = self.parse_yum_check_update(resp)
        else:
            if "rpmdb open failed" in err:
                self.json_out["Summary"] = \
                    "Failed to open rpmdb in image under test, " \
                    "scanner needs configured `yum` in image under test. " \
                    "%s" % str(err)
            elif err:
                self.json_out["Summary"] = \
                    "Error occured while processing yum updates. %s" % str(err)
                self.json_out["Successful"] = False
            # both err and resp are empty in this case
            else:
                self.json_out["Summary"] = \
                    "No RPM updates available."
                self.json_out["Successful"] = True

        self.json_out['Scan Results']['Package Updates'] = updates

    def parse_yum_check_update(self, data):
        resp = []

        # `data` will be str. Create a list
        ldata = data.split()

        for i in ldata:
            if ldata.index(i) % 3 == 0:
                resp.append(i)

        return resp

    def write_json_data(self):
        # make directory to write to
        os.makedirs(self.out_path)
        current_time = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
        self.json_out["Finished Time"] = current_time

        with open(self.op_file, "w") as f:
            f.write(json.dumps(self.json_out, indent=4))

    def return_os_release(self):
        """This method requires you to run self.check_release beforehand."""
        return self.json_out["Scan Results"]["OS Release"]


for d in dirs:
    # First the image scan

    # Initiate image scan object
    image_scan = ScanImageRootfs(d)

    # Check the release of image we're scanning
    image_scan.scan_release()

    # Check for yum updates
    image_scan.scan_yum_update()

    # Write scan results to json file
    image_scan.write_json_data()

    # Before we move to container scan

    # Check if the image is based on CentOS
    # os_release = image_scan.return_os_release()

    # if "CentOS Linux" not in os_release:
    #     print "Sorry, we can't help you scan non CentOS images at this point"
    #     sys.exit(1)

    # container_scan = ScanImageContainer(d)

    # container_scan.create_and_run_container()
    # container_scan.check_yum_update()
    # container_scan.write_json_data()
