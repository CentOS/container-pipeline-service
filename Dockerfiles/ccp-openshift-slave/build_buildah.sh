#!/bin/bash

yum install -y make \
    go-toolset-7 \
    device-mapper-devel \
    glib2-devel gpgme-devel \
    libassuan-devel \
    libseccomp-devel \
    ostree-devel \
    openssl-devel \
    runc \
    skopeo-containers
yum clean all

source /opt/rh/go-toolset-7/enable
go get github.com/cpuguy83/go-md2man
cp ~/go/bin/go-md2man /usr/local/bin/
mkdir /tmp/buildah && cd /tmp/buildah
export GOPATH=`pwd`
git clone https://github.com/containers/buildah ./src/github.com/containers/buildah
cd ./src/github.com/containers/buildah
make
make install
cp buildah /usr/local/bin/
