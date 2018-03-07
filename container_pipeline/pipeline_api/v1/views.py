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


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This class provides a view into the Project model.
    """
    queryset = Project.objects.all()
    serializer_class = serializers.ProjectSerializer

    def get_queryset(self):
        projects = Project.objects.all()
        p_name = self.request.query_params.get('name', None)
        if p_name:
            projects = projects.filter(name=p_name)
        return projects


class BuildViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This class provides a view into the Build model.
    """
    queryset = Build.objects.all().order_by('-start_time')
    serializer_class = serializers.BuildSerializer

    def get_queryset(self):
        builds = Build.objects.all.order_by('-start_time')

        b_project = self.request.query_params.get('project', None)
        b_status = self.request.query_params.get('status', None)
        # b_start_time = self.request.query_params.get('start_time', None)
        # b_end_time = self.request.query_params.get('end_time', None)

        if b_project:
            builds = builds.filter(project=b_project)
        if b_status:
            builds = builds.filter(status=b_status)

        return builds


class BuildPhaseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This model provides a view into the BuildPhase model.
    """
    queryset = BuildPhase.objects.all().order_by('-start_time')
    serializer_class = serializers.BuildPhaseSerializer

    def get_queryset(self):
        build_phases = BuildPhase.objects.all().order_by('-start_time')

        bp_build = self.request.query_params.get('build', None)
        bp_phase = self.request.query_params.get('phase', None)
        bp_status = self.request.query_params.get('status', None)

        if bp_build:
            build_phases = build_phases.filter(build=bp_build)
        if bp_phase:
            build_phases = build_phases.filter(phase=bp_phase)
        if bp_status:
            build_phases = build_phases.filter(status=bp_status)

        return build_phases


class RepoInfoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This class provides a view into the RepoInfo model.
    """
    queryset = RepoInfo.objects.all()
    serializer_class = serializers.RepoInfoSerializer


class PackageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This class provides a view into Package model.
    """
    queryset = Package.objects.all()
    serializer_class = serializers.PackageSerializer


class ContainerImageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This class provides a view into the ContainerImage model.
    """
    queryset = ContainerImage.objects.all()
    serializer_class = serializers.ContainerImageSerializer

    def get_queryset(self):
        container_images = ContainerImage.objects.all()

        ci_name = self.request.query_params.get('name', None)

        if ci_name:
            container_images = container_images.filter(name=ci_name)

        return container_images
