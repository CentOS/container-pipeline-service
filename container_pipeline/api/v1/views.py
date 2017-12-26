from container_pipeline.models.pipeline import Project, Build, BuildPhase, ContainerImage
from container_pipeline.models.tracking import RepoInfo, Package
from rest_framework import viewsets
from container_pipeline.api.v1 import serializers


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = serializers.ProjectSerializer


class BuildViewSet(viewsets.ModelViewSet):
    queryset = Build.objects.all().order_by('-start_time')
    serializer_class = serializers.BuildSerializer


class BuildPhaseViewSet(viewsets.ModelViewSet):
    queryset = BuildPhase.objects.all().order_by('-start_time')
    serializer_class = serializers.BuildPhaseSerializer


class RepoInfoViewSet(viewsets.ModelViewSet):
    queryset = RepoInfo.objects.all()
    serializer_class = serializers.RepoInfoSerializer


class PackageViewSet(viewsets.ModelViewSet):
    queryset = Package.objects.all()
    serializer_class = serializers.PackageSerializer


class ContainerImageViewSet(viewsets.ModelViewSet):
    queryset = ContainerImage.objects.all()
    serializer_class = serializers.ContainerImageSerializer
