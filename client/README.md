# Container Pipeline PoC

There was a quick meeting during the DevConf.cz 2016 about CentOS Container Pipeline, what it could consist of and how it could work. Not all details has been sketched out, but some ideas were thrown at the wall to see which one will stick.

Idea which I was pushing during the meeting was to use OpenShift as a workflow controller. To be more specific, to use OpenShift Template and a set of custom builds to define a workflow which will accept repository URL as input and will provide tested (production ready) image as output.

## User Story

I as an application developer want to build, test and deliver my containerized application on top of CentOS/Fedora base images so that I can focus on development and be sure images are always available and working for the app users.

## Key parts

My perception of the pipeline is that we want to provide a single input interface to the system (pipeline index) and don't limit ourselves in ways how to deliver the image (i.e. in case of Docker to push to any registry accessible from the pipeline infra). We obviously want to build an image provided by a user, we want to test it with a predefined set of tests and with tests provided by user, we want to deliver the image (i.e. push it to registry) and present logs in case of failures.

![Container Pipeline Diagram](https://docs.google.com/drawings/d/1Izkwa7b7pAM_mpiL6M_qkqOMP_-bzmo1C-IE1fZDGY4/pub?w=960&h=720)

1. Input Interface
    * A web UI/cli which allows user to provide at lease name of the project and repo URL. 
2. OpenShift
    * **Build** - Can be Atomic Reactor, result: image tagged as :test pushed
    * **Test** - Can be a script connecting to Jenkins, result: image tagged as :rc pushed
    * **Delivery** - A simple script to re-tag image to it's final name, result: image tagged as :latest or :vX.Y.Z pushed
3. Jenkins/CI
    * Infra where **Test** step in OpenShift connects to
4. Registry
    * Pulp or a registry provided by OpenShift, needs further investigation
5. (1.) Failure UI
    * Probably part of Input Interface, presenting logs from failed builds

## Proof of Concept

Main purpose of this repository is to show potential of OpenShift in solving above stated user story.

It covers points 2. and 3. from diagram - i.e. references an ADB Vagrantfile for easily runnable OpenShift and contains Dockerfiles for build, test and delivery images, build script and run script.

### Usage

To test Container Pipeline PoC, please follow the snippet below.

First, you will need to clone this repo. This PoC uses [ADB OpenShift Vagrant](https://github.com/projectatomic/adb-atomic-developer-bundle/blob/master/components/centos/centos-openshift-setup/Vagrantfile) box and thus you'll need to download it and *up* the box.

Make sure you have either don't have `projectatomic/adb` box on your machine, or you have the latest version (v1.7.0)

```
$ sudo vagrant box list
projectatomic/adb    (libvirt, 1.7.0)
```

Now to the demo itself...

```
git clone https://github.com/vpavlin/cccp-demo-openshift
cd cccp-demo-openshift
curl -O https://raw.githubusercontent.com/projectatomic/adb-atomic-developer-bundle/master/components/centos/centos-openshift-setup/Vagrantfile
sudo vagrant up
sudo vagrant ssh
```

There is potentially a bug in ADB 1.7.0 (at least for me - https://github.com/projectatomic/adb-atomic-developer-bundle/issues/243). If you hit it, you'll need to do:

```
sudo chmod +x /usr/bin/oadm
sudo systemctl restart openshift
```

You might want to see if OpenShift started successfully now by checking https://10.1.2.2:8443/console/

As the Vagrant box suggests, the login information you'll need for `oc login` command below are

* **Login:** admin
* **Password:** admin

```
oc login localhost:8443 -u admin -p admin --insecure-skip-tls-verify
/vagrant/build.sh
/vagrant/new-project.sh cccp-demo demo-proj https://github.com/vpavlin/cccp-demo-proj
```

If all goes well, the last command will print a URL where you can see builds progress and review logs (using the login information above).

Script `build.sh` creates images which are then used by OpenShift to fulfill individual steps of the workflow defined by `template.json`. Script `new-project.sh` represents an Input Interface to the system and accepts name of the project, name of the image which represents the output of pipeline and source repository URL (this URL has to contain Dockerfile).

```
[vagrant@centos7-adb ~]$ /vagrant/new-project.sh 
new-project.sh NAME REPO_URL
   NAME      Name of the project/namespace
   TAG       Name of the resulting image (image will be named NAME/TAG:latest)
   REPO_URL  URL of project repository containing Dockerfile
```

In case you want to start over, you need to remove the created project first and re-run `new-project.sh` (or just change the `NAME` parameter).

```
oc delete project cccp-demo
/vagrant/new-project.sh cccp-demo demo-proj https://github.com/vpavlin/cccp-demo-proj

```

### Template Objects

The template consists of OpenShift objects. The following paragraphs will describe each of them.

#### Parameters

This object represents a list of parameters which can be used to modify the behaviour of the steps described below.

* `SOURCE_REPOSITORY_URL` - The URL of the repository with your application source code
* `BUILD_TRIGGER_SECRET` - A secret to be used to trigger a build via Origin API (This is not used now, as OpenShift instance in Vagrant box does not support generic triggers)
* `TARGET_REGISTRY` - An URL of a registry where to push the final image
* `TARGET_NAMESPACE` - A namespace in the target registry where to push the final image
* `TAG` - Tag for the resulting image
* `REPO_BUILD_PATH` - Path to a directory containing a Dockerfile
* `REPO_TEST_PATH` - Path to tests in a repository (not used)

#### ImageStream

This object represents a connection between the steps of the workflow. Everytime a change happens to an image referenced by `${TAG}`, some action is trigged

#### Build - BuildConfig

BuildConfig named **Build** represents first step of the workflow - image build. You can review what happens in this step in [`run.sh`](run.sh) file. 

It simply clones a given repository and runs a Docker build in a given directory. The result is pushed as `${TAG}:test` which triggers **Test** step through ImageStream.

#### Test - BuildConfig

BuildConfig named **Test** represents second step of the workflow - image test. You can review what happens in this step in [`run-test.sh`](run-test.sh) file.

There is no interaction with CI (Jenkins). All it does is that it prints some messages and re-tags and pushes the image `${TAG}:rc` as if tests passed. The push triggers **Delivery** step through ImageStream

#### Delivery - BuildConfig

BuildConfig named **Delivery** represents second step of the workflow - image delivery. You can review what happens in this step in [`run-delivery.sh`](run-delivery.sh) file.

The only task of this step is to pull the `${TAG}:rc` image, tag it as `${TAG}:latest` and push to `${TARGET_REGISTRY}`. This step is not fully functional as in real world, it would have to authenticate itself against the target registry (which it does not)
