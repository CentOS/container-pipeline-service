#!/usr/bin/env python
import os
import sys

import yaml


def main(target_file_path, mock=False):
    cccp_yml_file = "mock_cccp.yml" if mock else "cccp.yml"
    stream = open(cccp_yml_file,'r')
    cccp_yml = yaml.load(stream)
    stream.close()
    print "==> Getting current directory"
    curr_dir = os.getcwd()
    print "==> Saving scripts for build process"

    job_id = cccp_yml.get("job-id")
    if not job_id:
        raise Exception("Missing or empty job-id field")

    test_skip = cccp_yml.get("test-skip")
    build_script_path = cccp_yml.get("build-script")
    if build_script_path:
        build_script_path = os.path.join(curr_dir, build_script_path)
        add_build_steps(target_file_path, "RUN ln -s "+build_script_path+" /usr/bin/build_script")
    else:
        echo_scripts("/build_script", "Build ")
        add_build_steps(target_file_path, "RUN ln -s /build_script /usr/bin/build_script")

    delivery_script = cccp_yml.get("delivery-script")
    if delivery_script:
        delivery_script_path = os.path.join(curr_dir, delivery_script)
        add_build_steps(target_file_path, "RUN ln -s "+delivery_script_path+" /usr/bin/delivery_script")
    else:
        echo_scripts("/delivery_scripts", "Delivery ")
        add_build_steps(target_file_path, "RUN ln -s /delivery_script /usr/bin/delivery_script")

    if not test_skip:
        test_script = cccp_yml.get("test-script")
        if not test_script:
            raise Exception("None or empty test script provided")
        test_script_path = os.path.join(curr_dir, test_script)
        add_build_steps(target_file_path, "RUN ln -s "+test_script_path+" /usr/bin/test_script")
    else:
        echo_scripts("/test_scripts", "Test ")
        add_build_steps(target_file_path, "RUN ln -s /test_script /usr/bin/test_script")

    print "==> scripts saved"


def echo_scripts(filepath,phase):
    fo = open(filepath, "w")
    fo.write("echo \""+phase+"Script not present\"")
    fo.close()


def add_build_steps(filepath,step):
    target_file = open(filepath, "a")
    target_file.write(step+"\n")
    target_file.close()

if __name__ == '__main__':
    main(sys.argv[1])
