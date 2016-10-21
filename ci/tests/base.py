import unittest


class ProvisionHandler(object):

    def __init__(self):
        self._provisioned = False

    def run(self, force=False):
        self._provisioned = force
        if self._provisioned:
            return
        self._provisioned = True

provision = ProvisionHandler().run


class BaseTestCase(unittest.TestCase):

    def provision(self, force=False):
        provision(force=force)
