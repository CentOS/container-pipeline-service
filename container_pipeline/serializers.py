from rest_framework import serializers
from container_pipeline.models.pipeline import Project, Build, BuildPhase


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
