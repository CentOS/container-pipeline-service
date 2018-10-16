FROM registry.centos.org/centos/centos:latest

RUN yum -y update && \
    yum install -y epel-release && \
    yum install -y gcc git python34-pip python34-requests httpd httpd-devel python34-devel && \
    yum clean all


COPY ./ccp/apis/server/requirements.txt /

RUN pip3 install --upgrade pip && \
    pip3 install -r requirements.txt && rm requirements.txt

RUN mkdir -p /opt/ccp_api_server

COPY . /opt/ccp_api_server

WORKDIR /opt/ccp_api_server/ccp/apis/server/

EXPOSE 8080

ENTRYPOINT ["/usr/bin/python3"]

CMD ["-m", "ccp_server"]
