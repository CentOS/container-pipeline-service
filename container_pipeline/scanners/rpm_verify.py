#!/usr/bin/python
"""RPM Verify Scan Class."""

from container_pipeline.scanners.base import Scanner


class ScannerRPMVerify(Scanner):
    """scanner-rpm-verify atomic scanner handler."""

    def __init__(self):
        """Scanner verify initialization."""
        self.scanner = "rpm-verify"
        self.result_file = "rpm_verify_scanner_results.json"

    def run(self, image):
        """
        Run the scanner-rpm-verify atomic scanner.

        Returns: Tuple stating the status of the execution and
        actual data(True/False, json_data)

        """
        super(ScannerRPMVerify, self).__init__(
            image=image,
            scanner=self.scanner,
            result_file=self.result_file)
        data = self.scan()

        # invoke base class's cleanup utility
        self.cleanup()

        return data
