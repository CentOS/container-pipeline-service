#!/usr/bin/env python
import os
import yaml

def main():
  stream = open("/set_env/cccp.yml",'r')
  cccp_yml = yaml.load(stream)
  stream.close()
  
  job_id = cccp_yml["job-id"]
  test_skip = cccp_yml["test-skip"]
  build_script = cccp_yml["build-script"]
  test_script = cccp_yml["test-script"]
  delivery_script = cccp_yml["delivery-script"]

  print "==> Getting current directory"
  curr_dir = os.getcwd()

  print "==> Saving scripts for build process"
  os.symlink(os.path.join(curr_dir,build_script),"/usr/bin/build_script")
  if(test_skip != true):
    os.symlink(os.path.join(curr_dir,test_script),"/usr/bin/test_script")

  os.symlink(os.path.join(curr_dir,delivery_script),"/usr/bin/delivery_script")
  print "==> scripts saved"

if __name__ == '__main__':
  main()
