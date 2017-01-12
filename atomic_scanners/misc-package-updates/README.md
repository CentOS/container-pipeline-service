Atomic scanner: misc-package-updates
--------------------------------

This is a container image scanner based on `atomic scan`. The goal of the
scanner is to scan CentOS based container images in the CentOS Community Container
Pipeline and generate relevant results.

Steps to use:

- Pull container image from **registry.centos.org**:

```
$ docker pull registry.centos.org/pipeline-images/misc-package-updates
```

- Install it using `atomic`:

```
$ atomic install registry.centos.org/pipeline-images/misc-package-updates
```


- Run the scanner on CentOS based images:

```
$ IMAGE_NAME=registry.centos.org/centos/centos atomic scan --scanner misc-package-updates registry.centos.org/centos/centos
```

Scanner needs an environment variable `IMAGE_NAME` set on the host system to be
able to scan the image and report the results.
