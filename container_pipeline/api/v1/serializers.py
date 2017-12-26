from rest_framework import serializers
from container_pipeline.models.pipeline import Project, Build, BuildPhase, ContainerImage
from container_pipeline.models.tracking import RepoInfo, Package


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"


class BuildSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Build
        fields = "__all__"


class BuildPhaseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = BuildPhase
        fields = "__all__"


class RepoInfoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = RepoInfo
        fields = "__all__"


class PackageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Package
        fields = "__all__"


class ContainerImageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ContainerImage
        fields = "__all__"
