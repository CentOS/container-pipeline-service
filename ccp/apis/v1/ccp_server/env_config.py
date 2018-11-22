import os


OPENSHIFT_VERSION = os.environ.get("OPENSHIFT_VERSION")
OPENSHIFT_URL = os.environ.get("OPENSHIFT_SERVER")
JENKINS_URL = os.environ.get("JENKINS_URL")
SERVICE_ACCOUNT_SECRET_MOUNT_PATH = "/run/secrets/kubernetes.io/serviceaccount"
