import subprocess

from django.db import models
from django.conf import settings


class Package(models.Model):
    name = models.CharField(max_length=200, db_index=True,
                            help_text="Package name")
    arch = models.CharField(max_length=20, db_index=True,
                            help_text="Architecture")
    version = models.CharField(max_length=100, help_text="Version")
    release = models.CharField(max_length=20, help_text="Release")

    created = models.DateTimeField(auto_now_add=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        db_table = 'packages'
        unique_together = ('name', 'arch', 'version', 'release')

    def __str__(self):
        return "{}-{}-{}.{}".format(self.name, self.version, self.release,
                                    self.arch)


class RepoInfo(models.Model):
    baseurls = models.TextField(max_length=2000, db_index=True,
                                help_text="Repo urls", unique=True)
    basearch = models.CharField(max_length=20, db_index=True)
    releasever = models.CharField(max_length=10, db_index=True)
    infra = models.CharField(max_length=50)

    class Meta:
        db_table = 'repo_info'

    def __str__(self):
        return self.baseurls


class ContainerImage(models.Model):
    name = models.CharField(max_length=200, db_index=True,
                            help_text="Image name", unique=True)
    packages = models.ManyToManyField(Package, related_name='images',
                                      help_text="Packages")
    parents = models.ManyToManyField('self', symmetrical=False,
                                     help_text="Parent images")
    repoinfo = models.ForeignKey(RepoInfo, null=True)

    to_build = models.BooleanField(default=False, db_index=True,
                                   help_text='Whether to build image or not')
    scanned = models.BooleanField(default=False, db_index=True,
                                  help_text='Whether the image is scanner')
    last_scanned = models.DateTimeField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        db_table = 'container_images'

    def __str__(self):
        return self.name

    @property
    def fullname(self):
        return '{}/{}'.format(settings.REGISTRY_ENDPOINT[0], self.name)

    @property
    def jobname(self):
        return self.name.replace(':', '-').replace('/', '-')

    def pull(self):
        docker_cmd = 'docker pull {name}'.format(name=self.fullname)
        return subprocess.check_output(docker_cmd, shell=True)

    def run(self, cmd):
        docker_cmd = (
            'docker run --rm --entrypoint "/bin/bash" {name} -c "{cmd}"'.
            format(name=self.fullname, cmd=cmd.replace('"', '\\"')))
        return subprocess.check_output(docker_cmd, shell=True)

    def trigger_build(self):
        if settings.JENKINS_USERNAME:
            cmd = (
                'java -jar {} -s {} build {} --username {} --password {}'
                .format(
                    settings.JENKINS_CLI,
                    settings.JENKINS_ENDPOINT,
                    self.jobname,
                    settings.JENKINS_USERNAME,
                    settings.JENKINS_PASSWORD)
            )
        else:
            cmd = (
                'java -jar {} -s {} build {}'.format(
                    settings.JENKINS_CLI,
                    settings.JENKINS_ENDPOINT,
                    self.jobname)
            )

        subprocess.check_call(cmd, shell=True)
