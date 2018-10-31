FROM registry.centos.org/centos/centos:latest

RUN yum -y update && \
    yum install -y epel-release && \
    yum install -y gcc git python34-pip python34-requests httpd httpd-devel python34-devel && \
    yum clean all

COPY ./ccp/apis/v1/server/requirements.txt /

RUN pip3 install --upgrade pip && \
    pip3 install -r requirements.txt && rm requirements.txt

ENV OPENSHIFT_VERSION="39"
ENV OPENSHIFT_URL=""
ENV JENKINS_URL=""

RUN yum -y install centos-release-openshift-origin${OPENSHIFT_VERSION} && \
    yum -y install origin-clients

RUN mkdir -p /opt/container-pipeline-service

ENV PYTHONPATH="/opt/container-pipeline-service"

COPY . /opt/container-pipeline-service

RUN useradd 1001 && usermod -aG 0 1001 && chown -R 1001:0 /opt/container-pipeline-service && chmod -R g+x /opt/container-pipeline-service

WORKDIR /opt/container-pipeline-service/ccp/apis/v1/server/

EXPOSE 8080

ENTRYPOINT ["/usr/bin/python3"]

CMD ["-m", "ccp_server"]

USER 1001
