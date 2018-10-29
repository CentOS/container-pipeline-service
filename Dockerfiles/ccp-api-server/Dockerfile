FROM registry.centos.org/centos/centos:latest

RUN yum -y update && \
    yum install -y epel-release && \
    yum install -y gcc git python34-pip python34-requests httpd httpd-devel python34-devel && \
    yum clean all

COPY ./ccp/apis/server/requirements.txt /

RUN pip3 install --upgrade pip && \
    pip3 install -r requirements.txt && rm requirements.txt

ENV OPENSHIFT_VERSION="39"
ENV ORIGIN_SERVER="https://localhost:8443"

RUN yum -y install centos-release-openshift-origin${OPENSHIFT_VERSION} && \
    yum -y install origin-clients

RUN mkdir -p /opt/ccp_api_server

ENV PYTHONPATH="/opt/ccp_api_server"

COPY . /opt/ccp_api_server

RUN useradd 1001 && usermod -aG 0 1001 && chown -R 1001:0 /opt/ccp_api_server && chmod -R g+x /opt/ccp_api_server

WORKDIR /opt/ccp_api_server/ccp/apis/server/

EXPOSE 8080

ENTRYPOINT ["/usr/bin/python3"]

CMD ["-m", "ccp_server"]

USER 1001
