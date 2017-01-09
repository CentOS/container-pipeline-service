Atomic scanner: container-capabilities-scanner
--------------------------------

###NOTE:

- This scanner requires you to:

    - mount Docker socket (`/var/run/docker.sock`) of host system to the atomic
      scan container.
    
    - share process namespace of host system with the atomic scan container

    - set label `RUN` in Dockerfile with appropriate `docker run` command

- This scanner hasn't been tested beyond simple `docker run` examples
  shared below

---


This is a container image scanner based on `atomic scan`. The goal of
the scanner is to scan CentOS based container images in the CentOS
Community Container Pipeline and generate relevant results.

This scanner scans container image for RUN label. A RUN label must
specify the `docker run` command for the image. The scanner checks for
various options like `--privileged`, `--security-opt`, `--net`,
etc. that provide a container with escalated privileges.

Steps to use:

- Pull container image from **registry.centos.org**:

    ```
    $ docker pull registry.centos.org/pipeline-images/container-capabilities-scanner
    ```

- Install it using `atomic`:

    ```
    $ atomic install registry.centos.org/pipeline-images/container-capabilities-scanner
    ```

- Consider below Dockerfile and resulting container image:


        $ cat Dockerfile
        FROM registry.centos.org/centos/centos

        LABEL RUN docker run -it --privileged --net=host --security-opt label=disable registry.centos.org/centos/centos bash

        $ docker build -t privileged-centos .

- Now run the scanner as below and check resulting output:
        
        $ IMAGE_NAME=privileged-centos atomic scan --scanner container-capabilities-scanner privileged-centos
        docker run -t --rm -v /etc/localtime:/etc/localtime -v /run/atomic/2017-04-06-05-55-32-547275:/scanin -v /var/lib/atomic/container-capabilities-scanner/2017-04-06-05-55-32-547275:/scanout:rw,Z -v /var/run/docker.sock:/var/run/docker.sock -e IMAGE_NAME=privileged-centos registry.centos.org/pipeline-images/container-capabilities-scanner python scanner.py
        
        Files associated with this scan are in /var/lib/atomic/container-capabilities-scanner/2017-04-06-05-55-32-547275.
        
        $ cat /var/lib/atomic/container-capabilities-scanner/2017-04-06-05-55-32-547275/1bbfb878505090d137863b1258709d9b28d7bd6a46bd5ebf627fbb6e0784ce4d/image_scan_results.json
        {
        "Scan Type": "check-capabilities",
        "CVE Feed Last Updated": "NA",
        "UUID": "1bbfb878505090d137863b1258709d9b28d7bd6a46bd5ebf627fbb6e0784ce4d",
        "Reference documentation": "http://www.projectatomic.io/blog/2016/01/how-to-run-a-more-secure-non-root-user-container/",
        "Scan Results": {
            "Container capabilities": "\nThis container uses privileged security switches:\n\n\u001b[1mINFO: --security-opt label=disable\u001b[0m \n      Disabling label separation turns off tools like SELinux and could allow processes from the container to break out onto your host system.\n\n\u001b[1mINFO: --net=host\u001b[0m \n      Processes in this container can listen to ports (and possibly rawip traffic) on the host's network.\n\n\u001b[1mINFO: --privileged\u001b[0m \n      This container runs without separation and should be considered the same as root on your system.\n\nFor more information on these switches and their security implications, consult the manpage for 'docker run'.\n\n"
        },
        "Successful": "true",
        "Finished Time": "2017-04-06-05-55-38-466022",
        "Start Time": "2017-04-06-05-55-38-160488",
        "Scanner": "Container Capabilities Scanner"
        }

Scanner needs an environment variable `IMAGE_NAME` set on the host
system to be able to scan the image and report the results.
