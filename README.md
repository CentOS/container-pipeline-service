To spin up things in an OpenShift cluster based on the contents in this
repository, please make sure you have a minishift based VM or a CentOS VM with
root privileges. You'll also need to spin up Docker Distribution (registry) on
same VM or different VM.

### Docker Distribution (registry) setup

The system on which you'd like to setup the registry, execute following
commands:

```bash
$ yum install -y docker-distribution
$ systemctl enable --now docker-distribution
```

Also make sure that the firewall rules are not blocking access to the registry
(port 5000 by default.)

### OpenShift setup

**Minishift:**

Start the minishift VM using below command:

```bash
$ minishift start  \
--disk-size 50GB  \
--memory 8GB  \
--iso-url centos  \
--openshift-version 3.9.0  \
--insecure-registry <registry-ip>:<port>
```

Memory and storage can be varied based on availability. It is recommended to
have 4GB memory and 20GB disk space as minimum. However, make sure to use
`--iso-url centos` part in above command as we have setup things on CentOS based
minishift VM.

**CentOS VM**

A CentOS VM with 8GB memory and 50GB disk space should suffice. You can adjust
the resources based on availability. It is recommended to have 4GB memory and
20GB disk space as minimum.

In the VM, install docker and enable openshift origin repos:

```bash
$ yum install -y docker git centos-release-openshift-origin
$ yum install -y origin-clients
```

Edit Docker config to support OpenShift's internal registry and the external
registry we created in earlier step. Update `/etc/docker/daemon.json`

```json
{
"insecure-registries":["172.30.0.0/16", "<registry-ip>:<port>"]
}
```

Now enable docker and bring up the oc cluster

```bash
$ systemctl enable --now docker
$ oc cluster up --public-hostname=<IP address of the VM>
```

This will bring up the OpenShift cluster with latest verion of OpenShift origin.

**Bringing up the service**

Once the VM is ready with OpenShift cluster in it, spin up a Jenkins server
that can be used by the Jenkins Pipeline buildconfigs. Also, since we're going
to be building images using Jenkins pods, we need to add few capabilities to
the Jenkins service account.

Do this on host system:

```bash
$ oc login -u developer
$ oc process -p MEMORY_LIMIT=1Gi openshift//jenkins-persistent| oc create -f -

# to enable parallel builds
$ oc set env dc/jenkins \
JENKINS_JAVA_OVERRIDES="-Dhudson.slaves.NodeProvisioner.initialDelay=0,-Dhudson.slaves.NodeProvisioner.MARGIN=50,-Dhudson.slaves.NodeProvisioner.MARGIN0=0.85"

$ oc login -u system:admin
$ oc adm policy add-scc-to-user privileged system:serviceaccount:${openshift-namespace}:jenkins
$ oc adm policy add-role-to-user system:image-builder system:serviceaccount:${openshift-namespace}:jenkins
```

where `openshift-namespace` is the name of the OpenShift project in which
you're working.

This spins up a persistent Jenkins deployment which has 1 GB memory alloted to
it. The Jenkins service spun up by this template is recognized and used by the
Jenkins Pipelines.

**Configuring DaemonSet**

Scanning is one of the build pipeline phase the service offers.
In scanning, we introspect the image built. In order to make scanning module
available on all the possible builder nodes, we configure and deploy
DaemonSet. The DeamonSet spins up a pod per builder node, which avails
a docker volume for all the containers on the node. The scan stage in pipeline
uses the volume for performing scan phase.

DaemonSet needs to be deployed using cluster admin.
Configure it with cluster admin user:

```bash
# on host system
$ git clone https://github.com/dharmit/ccp-openshift/
$ cd ccp-openshift
$ oc login -u system:admin
$ oc create -f daemon-set/scan_data.yml
```

Note: The labels and name of pod defined for DaemonSet are used in pipeline
[template](seed-job/template.yaml) to identify the container created using DaemonSet.
Please keep the mentioned fields intact in DaemonSet template.

Now, login to the OpenShift cluster as user `developer` and create a build from the buildconfig under
`seed-job` directory in cloned `ccp-openshift` repo:

```bash
# on host system
$ oc login -u developer
$ oc process -p PIPELINE_REPO=${PIPELINE_REPO}  \
-p PIPELINE_BRANCH=${PIPELINE_BRANCH}  \
-p REGISTRY_URL=${REGISTRY_URL}  \
-p NAMESPACE=`oc project -q`  \
-p FROM_ADDRESS=${FROM_ADDRESS}  \
-p SMTP_SERVER=${SMTP_SERVER} -f seed-job/buildtemplate.yaml | oc create -f -
```

If you're a developer working on your fork, export appropriate values for the
variables used above. Otherwise you can use the command:

```bash
$ oc process -p PIPELINE_REPO=https://github.com/dharmit/ccp-openshift  \
-p PIPELINE_BRANCH=master  \
-p REGISTRY_URL=${REGISTRY_URL}  \
-p NAMESPACE=`oc project -q`  \
-p FROM_ADDRESS=${FROM_ADDRESS}  \
-p SMTP_SERVER=${SMTP_SERVER} -f seed-job/buildtemplate.yaml | oc create -f -
```

`REGISTRY_URL` is the IP:port combination of remote registry. For example
`192.168.122.38:5000`.

`FROM_ADDRESS` is the address from which emails will be sent to the end users.
`SMTP_SERVER` is the server to be used to send emails.

Now check in the OpenShift web console under Build -> Pipelines and see if a
Jenkins Pipeline has been created. Be patient because the image being used is
quite large (2.2 GB) at the moment.

To be able to build multiple container images at the same time, edit the
Jenkins deployment and add an environment variable `JENKINS_JAVA_OVERRIDES` to
it with the value
`-Dhudson.slaves.NodeProvisioner.initialDelay=0,-Dhudson.slaves.NodeProvisioner.MARGIN=50,-Dhudson.slaves.NodeProvisioner.MARGIN0=0.85`.

Since you changed the configuration, wait for the a new deployment to take
effect. Once it's done, exec into the Jenkins pod and check the output of `ps
-ef`. The three configuration options we added above should up in the `java`
command as space-separated and not comma-separated. Refer [this
diff](https://github.com/openshift/openshift-docs/pull/7259/files?short_path=05f80f3#diff-05f80f3ab954ce57c630417065819109)
to ensure that values are passed properly.
