"""
This file has function defined which can be used by all
the submodules without lengthy import paths.
Specifically, this file instantiates the Meta model
with information, which will be part of every api response.
"""

from ccp.apis.server.ccp_server.models.meta import Meta

from datetime import datetime


def meta_obj(api_version="v1"):
    """
    Instantiates the Meta model and returns its
    object
    """
    return Meta(
        api_version=api_version,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
