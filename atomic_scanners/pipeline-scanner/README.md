Atomic scanner: pipeline-scanner
--------------------------------

This is a container image scanner based on `atomic scan`. The goal of the
scanner is to scan CentOS based Docker images in the CentOS Community Container
Pipeline and generate relevant results.

Steps to use:

- Pull Docker image from **registry.centos.org**:

```
$ docker pull registry.centos.org/pipeline-images/pipeline-scanner
```

- Install it using `atomic`:

```
$ atomic install registry.centos.org/pipeline-images/pipeline-scanner
```

- Mount the image's rootfs because by default `atomic scan` would mount it in
  read-only mode but we need read-write capability:

```
$ atomic mount -o rw centos:centos7 /mnt
```

Make sure you have `centos:centos7` available locally before you try to mount

- Run the scanner on CentOS based images:

```
$ atomic scan --scanner pipeline-scanner --rootfs=/mnt centos:centos7
```
