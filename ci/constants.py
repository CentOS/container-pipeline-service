import os

PROJECT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__),
                 '..')
)

DEPLOY_LOGS_PATH = "/root/deploy.logs"
JENKINS_HOSTNAME = "localhost"
JENKINS_HTTP_PORT = 8080
JENKINS_JAR_LOCATION = "/opt/jenkins-cli.jar"
CI_TEST_JOB_NAME = "bamachrn-python"
LINTER_RESULT_FILE = "linter_results.txt"
LINTER_STATUS_FILE = "linter_status.json"
CONTROLLER_WORK_DIR = "/root/container-pipeline-service/"
PEP8_CONF = ".pep8.conf"
