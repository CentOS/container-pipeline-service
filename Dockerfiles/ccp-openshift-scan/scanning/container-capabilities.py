#!/usr/bin/env python

# this module checks the image's RUN label and provide security concerns
# based on flags used in `docker run` command.
# the check args method is taken from
# github.com/projectatomic/atomic/blob/master/Atomic/backends/_docker.py

import sys


def check_args(cmd):
    """
    Check the arguments of the docker run command and provide feedback
    """
    found_sec_arg = False
    security_args = {
        '--privileged':
            'This container runs without separation and should be '
            'considered the same as root on your system.',
        '--cap-add':
            'Adding capabilities to your container could allow processes '
            'from the container to break out onto your host system.',
        '--security-opt label:disable':
            'Disabling label separation turns off tools like SELinux and '
            'could allow processes from the container to break out onto '
            'your host system.',
        '--security-opt label=disable':
            'Disabling label separation turns off tools like SELinux and '
            'could allow processes from the container to break out onto '
            'your host system.',
        '--net=host':
            'Processes in this container can listen to ports (and '
            'possibly rawip traffic) on the host\'s network.',
        '--pid=host':
            'Processes in this container can see and interact with all '
            'processes on the host and disables SELinux within the '
            'container.',
        '--ipc=host':
            'Processes in this container can see and possibly interact '
            'with all semaphores and shared memory segments on the host '
            'as well as disables SELinux within the container.'
    }

    for sec_arg in security_args:
        if sec_arg in cmd:
            if not found_sec_arg:
                print("\nThis container uses privileged "
                      "security switches:")
            print("\nINFO: {}\n\t{}".format(sec_arg, security_args[sec_arg]))
            found_sec_arg = True
    if found_sec_arg:
        print("\nFor more information on these switches and their "
              "security implications, consult the manpage for "
              "'docker run'.\n")


def run_scan(command):
    """
    Runs the container capabilities scan and prints error message
    if provided command is empty
    """
    if not command:
        print ("\n RUN label is not available in image under test.")
    else:
        check_args(command)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        example = ('python container-capabilities.py'
                   ' "docker run --privileged $IMAGE /bin/true"')
        print ("Please provide one argument as\n{}".format(example))
        sys.exit(1)

    try:
        cli_arg = sys.argv[1].strip()
        run_scan(cli_arg)
    except Exception as e:
        print ("Error occurred in Container Capabilities scanner execution.")
        print ("Error: %s".format(e))
        sys.exit(1)
