#!/usr/bin/python
"""pipeline scanner class."""

from container_pipeline.scanners.base import Scanner


class PipelineScanner(Scanner):
    """pipeline-scanner atomic scanner handler."""

    def __init__(self):
        self.scanner_name = "pipeline-scanner"
        self.result_file = "pipeline_scanner_results.json"

    def run(self, image):
        """
        Run the given scanner
        """
        super(PipelineScanner, self).__init__(
            image=image,
            scanner=self.scanner_name,
            result_file=self.result_file)
        self.mount_image()
        data = self.scan(rootfs=True, process_output=False)

        # invoke base class's cleanup utility, also unmount
        self.cleanup(unmount=True)

        return self.process_output(data)

    def process_output(self, json_data):
        """
        Process output based on its content.

        Process the output from the scanner, parse the json and
        add meaningful information based on validations
        """
        data = {}
        data["image_under_test"] = self.image
        data["scanner"] = self.scanner
        # if status of execution as False
        if json_data.get("status", False):
            data["msg"] = "Failed to run the scanner."
            data["logs"] = {}
        # elif check if there are available package updates
        elif json_data["Scan Results"]["Package Updates"]:
            data["msg"] = "RPM updates available for the image."
            data["logs"] = json_data
        else:
            data["msg"] = "No updates required."
            data["logs"] = {}
        return data
