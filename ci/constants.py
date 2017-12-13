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
