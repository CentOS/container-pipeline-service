from django.db import models


class Package(models.Model):
    name = models.CharField(max_length=200, db_index=True,
                            help_text="Package name")
    arch = models.CharField(max_length=20, db_index=True,
                            help_text="Architecture")
    version = models.CharField(max_length=100, help_text="Version")
    release = models.CharField(max_length=100, help_text="Release")

    created = models.DateTimeField(auto_now_add=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        db_table = 'packages'
        unique_together = ('name', 'arch', 'version', 'release')
        app_label = 'container_pipeline'

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
        app_label = 'container_pipeline'

    def __str__(self):
        return self.baseurls


