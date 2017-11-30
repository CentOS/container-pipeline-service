from rest_framework import serializers
from container_pipeline.models.pipeline import Project, Build, BuildPhase


class ProjectSerializerV1(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"


class BuildSerializerV1(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Build
        fields = "__all__"


class BuildPhaseSerializerV1(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = BuildPhase
        fields = "__all__"
