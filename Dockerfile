FROM registry.centos.org/centos/centos
MAINTAINER CentOS Community Container Pipeline <container-group@centos.org>

RUN yum update -y && \
    yum install python PyYAML -y && \
    yum clean all

ADD client/node.kubeconfig client/ca.crt /src/
ADD container_pipeline /src/container_pipeline
ADD oc /usr/bin/oc

ENV PYTHONPATH=$PYTHONPATH:/src/
WORKDIR /src
