#!/usr/bin/python
"""
This class is for checking container capabilities.

It reuses the scanner class for the methods.
"""

import os

from container_pipeline.scanners.base import Scanner


class ContainerCapabilities(Scanner):
    """Container Capabilities scan."""

    def __init__(self):
        """Scanner name and types."""
        self.scanner_name = "container-capabilities-scanner"
        self.result_file = "container_capabilities_scanner_results.json"

    def run(self, image):
        """Run the scanner on image under test."""
        # initializing a blank list that will contain results from all the
        # scan types of this scanner
        super(ContainerCapabilities, self).__init__(
            image=image,
            scanner=self.scanner_name,
            result_file=self.result_file)

        os.environ["IMAGE_NAME"] = self.image

        data = self.scan()

        return data
