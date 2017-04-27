# CentOS Community Container Pipeline

| Last PR Build | [![Build Status](https://ci.centos.org/view/Container/job/centos-container-pipeline-service-ci-pr/badge/icon)](https://ci.centos.org/view/Container/job/centos-container-pipeline-service-ci-pr/) |
|---------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

CentOS Community Container Pipeline is a service, to provide any Open Source developer(s), a platform for containerising their application(s). This process builds the application(s) from any arbitary git repository/repositories, package the built application along with its runtime in a container image, tests the image with help of test script and delivers to a publicly available registry. A user can anytime pull the tested image from that registry.

## User Story

As an application developer, I want to develop applications on a stack (django, golang, nodejs, redis, rabbitmq, etc.) of my choice using CentOS as the base platform. I want to make sure that the application is packaged into a container and updated  automatically every time I push changes to my Git (GitHub, BitBucket, Gitlab, etc.) repository; the resulting container image is scanned for updates, fixes, capabilities, and delivered to a public registry from where the users can pull the image and run the application. I also want the container image to be automatically rebuilt when an RPM package is updated in the repository or base image (`FROM` in Dockerfile) is updated.

## How does it work?

A developer working on an open-source project opens a pull request (PR) on [Container Index](https://github.com/CentOS/container-index/) to use Container Pipeline Service for building container images. Once the PR is merged, Container Pipeline Service lints the Dockerfile, builds the image for his/her project, scans it, pushes it to registry.centos.org (Web UI coming soon!), and finally notifies the developer via email.

Once a project is in the Container Index, the Container Pipeline Service service automatically tracks project's Git repo + branch for changes and rebuilds it every time there is a change.

**NOTE:** It might take some time for the build to finish as it depends on the number of jobs in the queue. If it's taking long, [contact us](#get-in-touch).

The entire flow can be summarized as below

![Container Pipeline Diagram](docs/diagrams/architecture.png)

1. **Project onboarding**

    Refer the [Container Index](https://github.com/CentOS/container-index).
    
2. **Jenkins based tracking**

    Tracks the developer's Git repository + branch for any change and triggers a new build on OpenShift when a change is pushed. Along with developer's repo, an update in base image or any of the RPMs which are a part of the image, also trigger a fresh build.

3. **Build the image**

    Build the container image using the targetfile (Dockerfile) and push it to OpenShift's internal registry. Result: image tagged as `:test` pushed to internal registry.

4. **Test the application**

     Can be a script (mentioned in the [yaml file](https://github.com/CentOS/container-index)) which runs tests on above image. Result: image tagged with a [hash based on date & time](https://github.com/CentOS/container-pipeline-service/blob/master/jenkinsbuilder/project-defaults.yml#L20) pushed to internal registry.
 
5. **Scan the image**
    
    Scan uses [atomic scan](https://github.com/projectatomic/atomic) tooling. Multiple atomic scanners are run on the built image and different checks are done - check if image has outdated RPM, npm, pip, gem packages and if image has tampered files present, etc. More details about the scanners can be found in `atomic_scanners` directory of this repo. Result: image tagged as `:rc` pushed to internal registry.
    
6. **Deliver to public registry**

    A simple script to re-tag image to it's final name based on value in the yaml file on Container Index. Result: image tagged with `:<desired_tag>` pushed to https://registry.centos.org. You can refer to [Container Pipeline Wiki page](https://wiki.centos.org/ContainerPipeline) to find currently available container images. This page is automatically updated when a new image is built in the Pipeline.

7. **Email to the Developer**

    An email is sent out the developer mentioning the status of the lint, build and scan processes and a link (s)he can use to read the detailed logs.
 
All the communication between the stages mentioned above happens via [beanstalkd](http://kr.github.io/beanstalkd/) tubes.   

## Contribute to Container Pipeline Service

We're always looking for ideas and improvements for the service! If you're interested in contributing to this repository, follow these simple steps:

- open an issue on GitHub describing the feature/bug
- fork the repository
- work on your branch for the fix of the issue
- raise a pull request

Before a PR is merged, it must:

- pass the CI done on [CentOS CI](https://ci.centos.org/)
- be code reviewed by the maintainers
- have maintainers' LGTM (Looks Good To Me)


## Generic hosts i.e. hosts not managed by Vagrant

This will allow you to bring up a single or multi-node setup of Container Pipeline
on various kinds of hosts (baremetal, a VPS, cloud or local VM, etc.) as long as they are accessible over SSH. This method uses Ansible for provisioning the hosts.

```bash
$ git clone https://github.com/CentOS/container-pipeline-service/
$ cd container-pipeline-service/provisions

# Copy sample hosts file and edit as needed
$ cp hosts.sample hosts

# Provision the hosts. This assumes that you have added the usernames,
# passwords or private keys used to access the hosts in the hosts file
# above
$ ansible-playbook -i hosts vagrant.yml
```

## <a href="contact"></a>Get in touch

For any queries get in touch with us on **#centos-devel** IRC channel on Freenode or send a mail to centos-devel@centos.org.
