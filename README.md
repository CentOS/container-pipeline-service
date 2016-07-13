# CentOS Community Container Pipeline

CentOS Community Container Pipeline(cccp) is a process, to provide any onesource developer a platform for containerising there application. This process builds the application from any arbitary git repository. Package the built application along with its runtime in a container image. Tests the image with help of test script and delivers to a publicly available registry. User can anytime pull the tested image from that registry.

## User Story

I as an application developer want to build, test and deliver my containerized application images so that I can focus on development and be sure images are always available and working for the app users.

## Key parts

We want to provide a single input interface to the system (pipeline index) and don't limit ourselves in ways how to deliver the image (i.e. in case of Docker to push to any registry accessible from the pipeline infra). We want to build an image provided by a user, we want to test it with a predefined set of tests and with tests provided by user, we want to deliver the image (i.e. push it to registry) and present logs in case of failures.

![Container Pipeline Diagram](https://docs.google.com/drawings/d/1sJfniMspEK9LI5CO9NsoSXhixbMqYNoJjPi9AKHNV-k/pub?w=960&h=720)

1. Input Interface
    * A web UI/cli which allows user to provide at least name of the project and repo URL.
    * This project tracks [cccp-index.yaml](https://github.com/kbsingh/cccp-index/blob/master/index.yml) as input to the build system.
2. OpenShift
    * **Build** - Can be Atomic Reactor, result: image tagged as :test pushed
    * **Test** - Can be a script connecting to Jenkins, result: image tagged as :rc pushed
    * **Delivery** - A simple script to re-tag image to it's final name, result: image tagged as :latest or :vX.Y.Z pushed
3. Jenkins/CI
    * Infra where **Test** step in OpenShift connects to
4. Registry
    * Pulp or a registry provided by OpenShift, deployed at https://registry.centos.org/
5. (1.) Failure UI
    * Probably part of Input Interface, presenting logs from failed builds


