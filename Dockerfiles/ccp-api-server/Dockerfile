FROM registry.centos.org/centos/centos:latest

RUN yum -y update && \
    yum install -y epel-release && \
    yum install -y gcc git python36-pip python36-requests httpd httpd-devel python36-devel && \
    yum clean all

COPY ./ccp/apis/v1/requirements.txt /

RUN pip3 install --upgrade pip && \
    pip3 install -r requirements.txt && rm requirements.txt

ENV OPENSHIFT_VERSION="311"
ENV OPENSHIFT_URL=""
ENV JENKINS_URL=""

RUN yum -y install centos-release-openshift-origin${OPENSHIFT_VERSION} && \
    yum -y install origin-clients

RUN mkdir -p /opt/container-pipeline-service

ENV PYTHONPATH="/opt/container-pipeline-service"

COPY . /opt/container-pipeline-service

RUN useradd -r -u 1001 -g 0 apirunner && chown -R 1001:0 /opt/container-pipeline-service && chmod -R g+x /opt/container-pipeline-service

WORKDIR /opt/container-pipeline-service/ccp/apis/v1/

RUN mkdir -p /var/index/repo && chmod 777 /var/index/repo

EXPOSE 8080

ENTRYPOINT ["/usr/bin/python3"]

CMD ["-m", "ccp_server"]

USER apirunner
