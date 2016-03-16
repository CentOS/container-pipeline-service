#!/usr/bin/env python
import os
import yaml

def main():
  stream = open("/set_env/cccp.yaml",'r')
  index_yaml = yaml.load(stream)
  stream.close()

  job_id = index_yaml[0]["project"]["name"]
  image_name = index_yaml[0]["project"]["image_name"]
  build_script = index_yaml[0]["project"]["build_script"]
  test_location = index_yaml[0]["project"]["test_location"]
  test_script = index_yaml[0]["project"]["test_script"]
  delivery_script = index_yaml[0]["project"]["delivery_script"]

  print "==> Getting current directory"
  curr_dir = os.getcwd()

  print "==> Saving scripts for build process"
  os.symlink(os.path.join(curr_dir,build_script),"/usr/bin/build_script")
  os.symlink(os.path.join(curr_dir,test_script),"/usr/bin/test_script")
  os.symlink(os.path.join(curr_dir,delivery_script),"/usr/bin/delivery_script")
  print "==> scripts saved"

if __name__ == '__main__':
  main()
