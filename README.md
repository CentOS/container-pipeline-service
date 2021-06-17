![CentOS Community Container Pipeline](docs/logos/logo.png)

----

CentOS Community Container Pipeline (CCCP) is an open-source platform to
containerize applications based on CentOS.

**CCCP:** Builds the application (from a git repository) → Packages with the
appropriate runtime → Scans the image → Pushes image to a public registry

----


## Use Case

I have a certain stack I develop with (be it Django, Golang, NodeJS, Redis,
RabbitMQ, etc.) using my CentOS as a base platform.

How do I package that application into a container that's updated automatically
every time I push changes? What about security and updates, how do I automate
that each time I push any changes?

That's where CCCP comes in.

CCCP will:

- Scan the image for updates, fixes, capabilities and push it to a public
  registry (by default, http://registry.centos.org)
- Automatically rebuild when a change is detected within the repository. Such
  as an update in base image (`FROM` in Dockerfile) or a `git push` to the
  project's git repository
- Notifications / alerts regarding build status and scan results (by e-mail)


## How do I host my application?

Similar to projects such as
[Homebrew](https://github.com/Homebrew/homebrew-core) it's as easy as opening
up a pull request.

A developer wishing to host their container image will open up a pull request
to the [CentOS Container Index](https://github.com/CentOS/container-index).

Once the pull request is merged, CCCP:

1. Links the Dockerfile
2. Builds the image
3. Scans / analyzes it
4. Pushes to [registry.centos.org](https://registry.centos.org)
5. Notifies the developer (email)

Once a project is in the [CentOS Container
Index](https://github.com/CentOS/container-index), the CentOS Container
Pipeline Service service automatically tracks the project's Git repo and branch
and rebuilds it every time there is a future change.

## How everything works

1. **Project onboard / the main "index"**

    First off, the pipeline points to an index. For the CentOS community and in
    our example, this refers to the: [CentOS Container
    Index](https://github.com/CentOS/container-index).

2. **Jenkins and OpenShift tracking**

    Jenkins is utilized in order to track each application's Git repository as
    well as branch for any changes. This triggers a new build on **OpenShift**
    when a change is pushed.

    Changes to the application's repository, update to the base image or any
    RPMs that are part of the image will trigger a new build

3. **Building the image**

    The container image is built by OpenShift.

4. **Scan and analyze the image**

    Scanning happens by running scripts in the container image to check for:
    - `yum` updates
    - updates for packages installed via `pip`, `npm` and `gem`
    - capabilities of the container created from resulting container image by
      analyzing `RUN` label in the Dockerfile
    - verify the installed RPMs

5. **Push to the public registry (https://registry.centos.org)**

    Finally, the image is pushed to https://registry.centos.org

6. **Notification**

    An email is sent out the developer mentioning the status of the build and
    scan process as well as a link to read the detailed logs.

## Architecture Diagram

Coming soon!

## Deploy your own pipeline

The service recently underwent an architecture change and is now completely
deployed on top of OpenShift. We have documented the steps in [docs](docs/)
directory. We recommend you to follow the docs and open up issues if something
doesn't work out.

## Contribute to the CentOS Community Container Pipeline Service

We're always looking for ideas and improvements for the service! If you're
interested in contributing to this repository, follow these simple steps:

- open an issue on GitHub describing the feature/bug
- fork the repository
- work on your branch for the fix of the issue
- raise a pull request

Before a PR is merged, it must:

- pass the CI done on [CentOS CI](https://ci.centos.org/)
- be code reviewed by the maintainers
- have maintainers' LGTM (Looks Good To Me)

## Community

__Chat (Mattermost):__ Our prefered method to reach the main developers is
through Mattermost at
[chat.openshift.io](https://chat.openshift.io/developers/channels/container-apps).

__IRC:__ If you prefer IRC, we can reached at **#centos-devel** on Libera.chat.

__Email:__ You could always e-mail us as well at centos-devel@centos.org

[Build Status]:
https://ci.centos.org/view/Container/job/centos-container-pipeline-service-ci-pr/
[Build Status Widget]:
https://ci.centos.org/view/Container/job/centos-container-pipeline-service-ci-pr/badge/icon
