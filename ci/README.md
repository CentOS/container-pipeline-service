# Continuous Integration

## Setup

- Install jenkins-job-builder: `sudo yum install python2-jenkins-job-builder -y`
- Configure `/etc/jenkins_jobs/jenkins_jobs.ini` Jenkins Job Builder as follows:
```
[jenkins]
user=<jenkins user>
password=<jenkins password>
url=<jenkins endpoint, e.g. https://ci.centos.org>
```

## Usage

```
jenkins-jobs update ci/job.yml
```

## CI jobs on ci.centos.org

- **[centos-container-pipeline-service-ci-master](https://ci.centos.org/view/Container/job/centos-container-pipeline-service-ci-master/)**: Runs on master branch of this repo at regular intervals.
- **[centos-container-pipeline-service-ci-pr](https://ci.centos.org/view/Container/job/centos-container-pipeline-service-ci-pr/)**: Runs on new pull requests created to this repo. It can also be triggered manually by commenting ``#dotests`` in the pull request by the project admins.
- **[centos-container-pipeline-service-ci-cleanup](https://ci.centos.org/view/Container/job/centos-container-pipeline-service-ci-cleanup/)**: Clean allocated resources on ci.centos.org on job success/failure
- **[centos-container-pipeline-service-container-index](https://ci.centos.org/view/Container/job/centos-container-pipeline-service-container-index/)**: Build centos container index from https://github.com/CentOS/container-index.git
