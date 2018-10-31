import os


OPENSHIFT_SERVER = os.environ.get("OPENSHIFT_SERVER") or \
                   "https://localhost:8443"
