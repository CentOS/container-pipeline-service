#!/usr/bin/bash
export DOCKER_REGISTRY="docker.io"

# The name of the OpenShift image.
export ORIGIN_IMAGE_NAME="openshift/origin:v1.1.3"

# The public IP address the VM created by Vagrant will get.
# You will use this IP address to connect to OpenShift web console.
export PUBLIC_ADDRESS=$(ip -f inet addr show eth0 2> /dev/null | grep 'inet' | awk '{ print $2}' | sed 's#/.*##')

export PUBLIC_HOST="bs.pco.centos.org"

# The directory where OpenShift will store the files.
# This should be "/var/lib/openshift" in case you're not using the :latest tag.
export ORIGIN_DIR="/var/lib/origin"

# The following steps are executed to provision OpenShift Origin:
# 1. Create a private network and set the Vagrant Box IP to *10.1.2.2*. If you want a different IP then change the **PUBLIC_ADDRESS** variable.
# 2. Pull latest the *openshift/origin* container from docker hub and tag it.
# 3. Create the required configuration file directories which OpenShift Origin uses.  Also set the SELinux flag to make sure they will work with *Enforcing* mode.
# 4. Run the OpenShift Origin docker container with various run options to make sure the required directory is mounted and the *host* network is used. **Note:** This takes about 15 seconds to start.
# 5. Check if the OpenShift Origin container has started as expected.  If there is an error, output the docker logs.
# 6. Make sure the ``oc`` and ``oadm`` binaries are available in the ADB Vagrant box.
# 7. Create a docker registry for use by the ``oc build`` command.  This command uploads local images to this registry.
# 8. Configure an OpenShift router so that apps can be accessed from the workstation.
# 9. Get the default templates and configure them.
# 10. Create a *test-admin user* and a *test project* for use by the developer.
# 11. Provide required configuration details for OpenShift web console and API.
# For More info about Openshift, please refer to `offical documents
# <https://docs.openshift.org/latest/welcome/index.html>`_.

  # On OS X you can enable Landrush to expose OpenShift routes to the host
  # Install the Landrush plugin 'vagrant plugin install landrush'
  # and comment in the lines below
  # This won't work on Windows and on Linux the TLD ending on .local might cause
  # problems
  # config.vm.hostname = "#{PUBLIC_HOST}"
  # config.landrush.enabled = true
  # config.landrush.host_ip_address = "#{PUBLIC_ADDRESS}"
  # config.landrush.tld = "#{PUBLIC_HOST}"
  # config.landrush.guest_redirect_dns = false

sed -i.back '/# INSECURE_REGISTRY=*/c\INSECURE_REGISTRY="--insecure-registry 172.30.0.0/16"' /etc/sysconfig/docker
systemctl restart docker.service

docker inspect openshift/origin &>/dev/null && exit 0
echo "[INFO] Pull the #{ORIGIN_IMAGE_NAME} Docker image ..."
docker pull ${ORIGIN_IMAGE_NAME}
docker tag ${DOCKER_REGISTRY}/${ORIGIN_IMAGE_NAME} ${ORIGIN_IMAGE_NAME}

echo "[INFO] Start the OpenShift server ..."
# Prepare directories for bind-mounting
dirs=(openshift.local.volumes openshift.local.config openshift.local.etcd)
for d in ${dirs[@]}; do
  mkdir -p ${ORIGIN_DIR}/${d} && chcon -Rt svirt_sandbox_file_t ${ORIGIN_DIR}/${d}
done
################New Run command###############
sudo docker run -d --name "origin" \
        --privileged --pid=host --net=host \
        -v /:/rootfs:ro -v /var/run:/var/run:rw -v /sys:/sys -v /var/lib/docker:/var/lib/docker:rw \
        -v /var/lib/origin/openshift.local.volumes:/var/lib/origin/openshift.local.volumes:rslave \
        openshift/origin start
##############################################
docker run -d --name "origin" --privileged --net=host --pid=host -v /:/rootfs:ro -v /var/run:/var/run:rw -v /sys:/sys:ro -v /var/lib/docker:/var/lib/docker:rw -v ${ORIGIN_DIR}/openshift.local.volumes:${ORIGIN_DIR}/openshift.local.volumes:z -v ${ORIGIN_DIR}/openshift.local.config:${ORIGIN_DIR}/openshift.local.config:z -v ${ORIGIN_DIR}/openshift.local.etcd:${ORIGIN_DIR}/openshift.local.etcd:z ${ORIGIN_IMAGE_NAME} start --master="https://${PUBLIC_ADDRESS}:8443" --etcd-dir="${ORIGIN_DIR}/openshift.local.etcd" --cors-allowed-origins=.*

sleep 50 # Give OpenShift 15 seconds to start

#state=$(docker inspect -f "{{.State.Running}}" origin)
#if [[ "${state}" != "true" ]]; then
#      >&2 echo "[ERROR] OpenShift failed to start:"
#      docker logs origin
#      exit 1
#    fi
#  SHELL

binaries=(oc oadm)
for n in ${binaries[@]}; do
  [ -f /usr/bin/${n} ] && continue
  echo "[INFO] Copy the OpenShift '${n}' binary to host /usr/bin/${n}..."
  docker run --rm --entrypoint=/bin/cat ${ORIGIN_IMAGE_NAME} /usr/bin/${n} > /usr/bin/${n}
  chmod +x /usr/bin/${n}
done

echo "export OPENSHIFT_DIR=${ORIGIN_DIR}/openshift.local.config/master" > /etc/profile.d/openshift.sh
export OPENSHIFT_DIR=${ORIGIN_DIR}/openshift.local.config/master

export KUBECONFIG=${OPENSHIFT_DIR}/admin.kubeconfig
chmod go+r ${KUBECONFIG}
# Create Docker Registry
if [ ! -f ${ORIGIN_DIR}/configured.registry ]; then
  echo "[INFO] Configure Docker Registry ..."
  #echo '{"kind":"ServiceAccount","apiVersion":"v1","metadata":{"name":"registry"}}' | oc create -f -
  #oc get scc privileged -o json | sed '/\"users\"/a \"system:serviceaccount:default:registry\",' | oc replace scc privileged -f -
  oadm registry --create --credentials=${OPENSHIFT_DIR}/openshift-registry.kubeconfig || exit 1 #--mount-host=/registry || exit 1
  oadm policy add-scc-to-group anyuid system:authenticated || exit 1
  touch ${ORIGIN_DIR}/configured.registry
fi
sleep 50 #let the registry run in privileged mode

# For router, we have to create service account first and then use it for
# router creation.
if [ ! -f ${ORIGIN_DIR}/configured.router ]; then
  echo "[INFO] Configure HAProxy router ..."
  echo '{"kind":"ServiceAccount","apiVersion":"v1","metadata":{"name":"router"}}' | oc create -f -
  oc get scc privileged -o json | sed '/\"users\"/a \"system:serviceaccount:default:router\",' | oc replace scc privileged -f -
  oadm router --create --credentials=${OPENSHIFT_DIR}/openshift-router.kubeconfig --service-account=router
  touch ${ORIGIN_DIR}/configured.router
fi
sleep 50 #let the router run

export KUBECONFIG=${OPENSHIFT_DIR}/admin.kubeconfig
if [ ! -f ${ORIGIN_DIR}/configured.templates ]; then
  echo "[INFO] Installing OpenShift templates ..."
  ose_tag=ose-v1.2.0-1
  template_list=(
    # Image streams
    https://raw.githubusercontent.com/openshift/origin/master/examples/image-streams/image-streams-rhel7.json
    https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/jboss-image-streams.json
    # DB templates
    https://raw.githubusercontent.com/openshift/origin/master/examples/db-templates/mongodb-ephemeral-template.json
    https://raw.githubusercontent.com/openshift/origin/master/examples/db-templates/mongodb-persistent-template.json
    https://raw.githubusercontent.com/openshift/origin/master/examples/db-templates/mysql-ephemeral-template.json
    https://raw.githubusercontent.com/openshift/origin/master/examples/db-templates/mysql-persistent-template.json
    https://raw.githubusercontent.com/openshift/origin/master/examples/db-templates/postgresql-ephemeral-template.json
    https://raw.githubusercontent.com/openshift/origin/master/examples/db-templates/postgresql-persistent-template.json
    # Jenkins
    https://raw.githubusercontent.com/openshift/origin/master/examples/jenkins/jenkins-ephemeral-template.json
    https://raw.githubusercontent.com/openshift/origin/master/examples/jenkins/jenkins-persistent-template.json
    # Node.js
    https://raw.githubusercontent.com/openshift/nodejs-ex/master/openshift/templates/nodejs-mongodb.json
    https://raw.githubusercontent.com/openshift/nodejs-ex/master/openshift/templates/nodejs.json
    # EAP
    https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/eap/eap64-amq-persistent-s2i.json
    https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/eap/eap64-amq-s2i.json
    https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/eap/eap64-basic-s2i.json
    https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/eap/eap64-https-s2i.json
    https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/eap/eap64-mongodb-persistent-s2i.json
    https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/eap/eap64-mongodb-s2i.json
    https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/eap/eap64-mysql-persistent-s2i.json
    https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/eap/eap64-mysql-s2i.json
    https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/eap/eap64-postgresql-persistent-s2i.json
    https://raw.githubusercontent.com/jboss-openshift/application-templates/${ose_tag}/eap/eap64-postgresql-s2i.json
  )

  for template in ${template_list[@]}; do
    echo "[INFO] Importing template ${template}"
    oc create -f $template -n openshift >/dev/null
  done
  touch ${ORIGIN_DIR}/configured.templates
fi
    
export KUBECONFIG=${OPENSHIFT_DIR}/admin.kubeconfig
if [ ! -f ${ORIGIN_DIR}/configured.templates ]; then
  echo "[INFO] Installing OpenShift templates ..."
  for name in $(find /opt/openshift/templates -name '*.json'); do
    oc create -f $name -n openshift >/dev/null
  done
  touch ${ORIGIN_DIR}/configured.templates
fi

    
echo "[INFO] Create 'test-admin' user and 'test' project ..."
if [ ! -f ${ORIGIN_DIR}/configured.user ]; then
  oadm policy add-role-to-user view test-admin --config=${OPENSHIFT_DIR}/admin.kubeconfig
  oc login https://${PUBLIC_ADDRESS}:8443 -u test-admin -p test --certificate-authority=${OPENSHIFT_DIR}/ca.crt &>/dev/null
  oc new-project test --display-name="OpenShift 3 Sample" --description="This is an example project to demonstrate OpenShift v3" &>/dev/null
  sudo touch ${ORIGIN_DIR}/configured.user
fi


echo "==> Building cccp-build image"
docker build -t cccp-build -f ./Dockerfile.build . || exit 1
echo "==> Building cccp-test image"
docker build -t cccp-test -f ./Dockerfile.test . || exit 1
echo "==> Building cccp-delivery image"
docker build -t cccp-delivery -f ./Dockerfile.delivery . || exit 1
echo "==> Uploading template to OpenShift"

