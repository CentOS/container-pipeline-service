import os

from Atomic import run
from Atomic.backends._docker import DockerBackend


def run_scanner(image):
    run_object = run.Run()
    run_object.image = image
    return DockerBackend.check_args(run_object.get_label("RUN"))

if __name__ == "__main__":
    run_scanner(os.environ.get("IMAGE_NAME"))
