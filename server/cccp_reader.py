#!/usr/bin/env python
import os
import sys
import yaml
from shutil import copyfile

def main():
  target_file_path = sys.argv[1]
  stream = open("cccp.yml",'r')
  cccp_yml = yaml.load(stream)
  stream.close()
  print "==> Getting current directory"
  curr_dir = os.getcwd()
  print "==> Saving scripts for build process"
  got_build_script = 0;
  got_test_script = 0;
  got_delivery_script = 0;

  for key, value in cccp_yml.iteritems():
    if(key == "job-id"):
      job_id = cccp_yml["job-id"]

    if(key == "test-skip"):
      test_skip = cccp_yml["test-skip"]

    if(key == "build-script"):
      build_script_path = cccp_yml["build-script"]
      build_script_path = os.path.join(curr_dir,build_script_path)
      add_build_steps(target_file_path,"RUN ln -s "+build_script_path+" /usr/bin/build_script")
      got_build_script=1;

    if(key == "test-script"):
      test_script = cccp_yml["test-script"]
      if(test_skip != True):
        test_script_path = os.path.join(curr_dir,test_script)
        add_build_steps(target_file_path,"RUN ln -s "+test_script_path+" /usr/bin/test_script")
        got_test_script=1;

    if(key == "delivery-script"):
      delivery_script = cccp_yml["delivery-script"]
      delivery_script_path = os.path.join(curr_dir,delivery_script)
      add_build_steps(target_file_path,"RUN ln -s "+delivery_script_path+" /usr/bin/delivery_script")
      got_delivery_script=1;

  if(got_build_script == 0):
    echo_scripts("/build_script","Build ");
    add_build_steps(target_file_path,"RUN ln -s /build_script /usr/bin/build_script")

  if(got_test_script == 0):
    echo_scripts("/test_scripts","Test ");
    add_build_steps(target_file_path,"RUN ln -s /test_script /usr/bin/test_script")

  if(got_delivery_script == 0):
    echo_scripts("/delivery_scripts","Delivery ");
    add_build_steps(target_file_path,"RUN ln -s /delivery_script /usr/bin/delivery_script")


  print "==> scripts saved"

def echo_scripts(filepath,phase):
  fo = open(filepath,"w");
  fo.write("echo \""+phase+"Script not present\"");
  fo.close();

def add_build_steps(filepath,step):
  target_file = open(filepath,"a");
  target_file.write(step+"\n")
  target_file.close()

if __name__ == '__main__':
  main()
