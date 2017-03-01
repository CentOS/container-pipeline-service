SCANNERS_OUTPUT = {
        "registry.centos.org/pipeline-images/pipeline-scanner": [
            "image_scan_results.json"],
        "registry.centos.org/pipeline-images/misc-package-updates": [
            "image_scan_results.json"],
        "registry.centos.org/pipeline-images/scanner-rpm-verify": [
            "RPMVerify.json"]
}

SCANNERS_RESULTFILE = {
        "registry.centos.org/pipeline-images/pipeline-scanner": [
            "pipeline_scanner_results.json"],
        "registry.centos.org/pipeline-images/misc-package-updates": [
            "misc_package_updates_scanner_results.json"],
        "registry.centos.org/pipeline-images/scanner-rpm-verify": [
            "RPMVerify_scanner_results.json"]
}

LINTER_RESULTFILE = "linter_results.txt"

LOGS_URL_BASE= "https://registry.centos.org/pipeline-logs/"
LOGS_DIR = "/srv/pipeline-logs/"
