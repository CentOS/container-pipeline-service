#!/bin/python

from subprocess import check_call, CalledProcessError
import random
import string
import os

class DependencyChecker:

    @staticmethod
    def execcmd(cmd):
        """Executes a cmd list and returns true if cmd executed correctly."""

        success = True

        try:
            check_call(cmd)
            success = True

        except CalledProcessError:
            success = False

        return success

    def __init__(self, registryurl="https://registry.centos.org", checkv1=True, checkv2=True):

        self._registryURL = registryurl
        self._checkV1 = checkv1
        self._checkV2 = checkv2
        self._tagsdumpfiles = []

        return

    def _fnamegenerator(self, size=6, chars=string.ascii_uppercase + string.digits):

        return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(size))

    def _wgetchecker(self, theurl):

        success = True

        jsonfile = "tagsdump_" + self._fnamegenerator()
        self._tagsdumpfiles.append(jsonfile)

        cmd = ["wget", "--output-document=" + jsonfile, theurl]

        step1_success = DependencyChecker.execcmd(cmd)

        if step1_success:

            step2_success = "latest" in open(jsonfile).read()
            success = step2_success

        else:

            success = step1_success

        return success

    def checkdependencies(self, dependencylist):

        success = True
        s1 = False
        s2 = False
        testslist = []

        for item in dependencylist:

            v1url = str.format("{0}/v1/repositories/{1}/tags", self._registryURL, item)
            v2url = str.format("{0}/v2/repositories/{1}/tags", self._registryURL, item)

            if self._checkV1:

                print "CHECKING V1 REGISTRY..."
                s1 = self._wgetchecker(v1url)

            if self._checkV2:

                print "CHECKING V2 REGISTRY..."
                s2 = self._wgetchecker(v2url)

            testslist.append((self._checkV1 and s1) or (self._checkV2 and s2))

        print "CLEANING UP..."
        for item in self._tagsdumpfiles:

            if os.path.exists(item):
                os.remove(item)

            if False in testslist:

                success = False

        return success

if __name__ == '__main__':

    print "This main is only for testing purposes : \n"
    dc = DependencyChecker()

    print "Checking valid name centos/c7-cockpit-kubernetes"
    print "\nStatus : " + str(dc.checkdependencies(["centos/c7-cockpit-kubernetes"]))

    print "\nChecking invalid name centos/c7-cockpit-kubernetess"
    print "\nStatus : " + str(dc.checkdependencies(["centos/c7-cockpit-kubernetess"]))