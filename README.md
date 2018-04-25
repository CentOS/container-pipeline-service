To spin up things in an OpenShift cluster based on the contents in this
repository, please make sure you have a
[minishift](https://github.com/minishift/minishift/) based VM started up. We've
not tested this against anything other than minishift.

We used following command to start a minishift environment:

```bash
$ minishift start --disk-size 50GB --memory 8GB --iso-url centos --openshift-version 3.9.0
```

But the resources can be varied based on availability. However, make sure to
use `--iso-url centos` part in above command as we have setup things on CentOS
based minishift VM.

Once the VM is ready, clone this repo on host system (not the VM). Login to the
OpenShift cluster using `oc` and create a build from the buildconfig under
`seed-job` directory:

```bash
# on host system
$ git clone https://github.com/dharmit/ccp-openshift/
$ cd ccp-openshift
$ oc login
$ oc create -f seed-job/buildconfig.yaml
```

A Jenkins server will be started in the OpenShift cluster. To ensure that it's
able to build containers, give it appropriate privilege:

```bash
$ oc adm policy add-role-to-user system:image-builder system:serviceaccount:myproject:jenkins
```

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
