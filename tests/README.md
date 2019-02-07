## Tests

## Setup

Ensure that the container-pipeline-service project directory is in PYTHONPATH.

``export PYTHONPATH=/path/to/container-pipeline-service:$PYTHONPATH``

### Nomenclature

Add a test package or module for a feature with a name of the form
``test_(?P<index>\d\d)_(?P<feature>\w+)(?:.py)?``, for example,

- ``test_00_openshift`` is a test package
- ``test_10_scanner.py`` is a test module for scanner


where

- **index** is used to run tests. order
- **feature** is the name of a feature or project component


Any module/package name should start with the prefix ``test``.  You can
follow the same patten when adding test modules inside a test package.


### How to write tests

``` python
from tests.base import BaseTestCase

# utitliy methods
from ci.lib import _print


class TestSomeFeature(BaseTestCase):

    # if you want to add something to test setup
    def setUp(self):
        super(TestSomeFeature, self).setUp()
        # your code goes here

    def test_00_first_test_case(self):
        # some code

        # utility method to run provisioning. If the system has been
        # provisioned already, it will just skip provisioning. However,
        # if you want to provision the system anyhow, pass
        # force=True as an keyword argument.
        self.provision()

        # utility method to run command on remote/local machines
        # if host arg is not provided, it defaults to running the command
        # on the local machine
        output = self.run_cmd('ls -la', user='root', host='192.168.10.20')

    def test_01_second_test_case(self):
        # some code

```

### Configuring hosts to test

By default, the hosts point to a multinode vagrant setup. You can customize it
by exporting a similar JSON to an env variable **CCCP_CI_HOSTS**:

``` json
{
  "jenkins_master": {
    "host": "192.168.100.100", 
    "remote_user": "vagrant", 
    "private_key": "~/.vagrant.d/insecure_private_key"
  }, 
  "controller": {
    "inventory_path": "provisions/hosts.vagrant", 
    "host": null, 
    "private_key": "~/.vagrant.d/insecure_private_key", 
    "user": "vagrant"
  }, 
  "openshift": {
    "host": "192.168.100.201", 
    "remote_user": "vagrant", 
    "private_key": "~/.vagrant.d/insecure_private_key"
  }, 
  "jenkins_slave": {
    "host": "192.168.100.200", 
    "remote_user": "vagrant", 
    "private_key": "~/.vagrant.d/insecure_private_key"
  }
}
```
