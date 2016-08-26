Atomic scanner: scanner-rpm-verify
--------------------------------

This is a container image scanner based on `atomic scan`. The goal of this
scanner is to scan container images by verifying and reporting the installed
RPM packages.

Steps to use:

- Pull Docker image from **registry.centos.org**:

```
$ docker pull registry.centos.org/pipeline-images/scanner-rpm-verify
```

- Install it using `atomic`:

```
$ atomic install registry.centos.org/pipeline-images/scanner-rpm-verify
```

- Mount the image's rootfs because by default `atomic scan` would mount it in
  read-only mode but we need read-write capability:

```
$ sudo atomic scan --scanner rpm-verify <image-to-scan>
```
