FROM registry.centos.org/centos/centos
MAINTAINER CentOS Community Container Pipeline <container-group@centos.org>

RUN yum update -y && \
    yum install python PyYAML -y && \
    yum clean all

RUN yum install epel-release -y && \
    yum install python-pip -y && \
    yum remove epel-release -y && \
    yum clean all

RUN pip install raven --upgrade

ADD node.kubeconfig ca.crt /opt/cccp-service/
ADD container_pipeline /opt/cccp-service/container_pipeline
ADD oc /usr/bin/oc

ENV PYTHONPATH=$PYTHONPATH:/opt/cccp-service/
WORKDIR /opt/cccp-service
