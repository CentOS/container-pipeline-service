from container_pipeline.models.pipeline import Project, Build, BuildPhase, ContainerImage
from container_pipeline.models.tracking import RepoInfo, Package
from rest_framework import viewsets
from container_pipeline.pipeline_api.v1 import serializers

"""
moduleauthor: The Container Pipeline Service Team

This module contains views for v1 api of the service
service. Its purpose is to make the data available
at the API endpoint.
"""


class ProjectViewSet(viewsets.ModelViewSet):
    """
    This class provides a view into the Project model.
    """
    queryset = Project.objects.all()
    serializer_class = serializers.ProjectSerializer

    def get_queryset(self):
        projects = Project.objects.all()
        p_name = self.request.QUERY_PARAMS.get('name', None)
        if p_name:
            projects = projects.filter(name=p_name)
        return projects


class BuildViewSet(viewsets.ModelViewSet):
    """
    This class provides a view into the Build model.
    """
    queryset = Build.objects.all().order_by('-start_time')
    serializer_class = serializers.BuildSerializer


class BuildPhaseViewSet(viewsets.ModelViewSet):
    """
    This model provides a view into the BuildPhase model.
    """
    queryset = BuildPhase.objects.all().order_by('-start_time')
    serializer_class = serializers.BuildPhaseSerializer


class RepoInfoViewSet(viewsets.ModelViewSet):
    """
    This class provides a view into the RepoInfo model.
    """
    queryset = RepoInfo.objects.all()
    serializer_class = serializers.RepoInfoSerializer


class PackageViewSet(viewsets.ModelViewSet):
    """
    This class provides a view into Package model.
    """
    queryset = Package.objects.all()
    serializer_class = serializers.PackageSerializer


class ContainerImageViewSet(viewsets.ModelViewSet):
    """
    This class provides a view into the ContainerImage model.
    """
    queryset = ContainerImage.objects.all()
    serializer_class = serializers.ContainerImageSerializer
