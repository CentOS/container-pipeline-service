from django.conf.urls import url, include
from rest_framework import routers

from container_pipeline.lib import constants
from container_pipeline.pipeline_api.v1 import views

"""
moduleauthor: The Container Pipeline Service Team

This module handles setting up the routes for v1 api of the
service.
"""


def get_v1_urls():
    """
    Gets all routed urls for the api's v1 endpoint
    :return: A list of url objects.
    """
    urls = []
    router1 = routers.DefaultRouter()
    router1.register(r'/projects', views.ProjectViewSet)
    router1.register(r'/builds', views.BuildViewSet)
    router1.register(r'/build-phases', views.BuildPhaseViewSet)
    router1.register(r'/container-image', views.ContainerImageViewSet)
    urls += [
        url(constants.V1_ENDPOINT, include(router1.urls))
    ]

    router2 = routers.DefaultRouter()
    router2.register(r'/package', views.PackageViewSet)
    router2.register(r'/repo-info', views.RepoInfoViewSet)
    urls += [
        url(constants.V1_RPM_ENDPOINT, include(router2.urls))
    ]
    return urls
