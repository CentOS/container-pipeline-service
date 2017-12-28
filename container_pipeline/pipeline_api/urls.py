from container_pipeline.pipeline_api.v1.urls import get_v1_urls

"""
moduleauthor: The Container Pipeline Service Team

This module collects all routes for the API and makes them available
to be added to top level urlpatterns.
"""


def get_api_urls():
    """
    Gets the routed urls from accross all API endpoints.
    :return: A list of url objects.
    """
    # urls = []
    # urls += get_v1_urls()
    return get_v1_urls()
