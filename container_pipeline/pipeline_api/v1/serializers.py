from rest_framework import serializers
from container_pipeline.models.pipeline import Project, Build, BuildPhase, ContainerImage
from container_pipeline.models.tracking import RepoInfo, Package

"""
moduleauthor: The Container Pipeline Service Team

This module contains Model Serializers for v1 api of the service
service. Its purpose is to serialize the models so that api views
can make use of the data.
"""


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    """
    This class serializes the Project model.
    """
    class Meta:
        model = Project
        fields = "__all__"


class BuildSerializer(serializers.HyperlinkedModelSerializer):
    """
    This class serializes the Build model.
    """
    class Meta:
        model = Build
        fields = "__all__"


class BuildPhaseSerializer(serializers.HyperlinkedModelSerializer):
    """
    This class serializes the BuildPhase model.
    """
    class Meta:
        model = BuildPhase
        fields = "__all__"


class RepoInfoSerializer(serializers.HyperlinkedModelSerializer):
    """
    This class serializes the RepoInfo model.
    """
    class Meta:
        model = RepoInfo
        fields = "__all__"


class PackageSerializer(serializers.HyperlinkedModelSerializer):
    """
    This class serializes the Package model.
    """
    class Meta:
        model = Package
        fields = "__all__"


class ContainerImageSerializer(serializers.HyperlinkedModelSerializer):
    """
    This class serializes the ContainerImage model.
    """
    class Meta:
        model = ContainerImage
        fields = "__all__"
