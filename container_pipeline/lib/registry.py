from container_pipeline.utils import request_url, rm
import json
from os import path


class RegistryInfo(object):
    """Stores/Caches metadata from specified registry"""

    def __init__(self, registry_host, registry_port, registry_secure):
        self._registry_url = str.format(
            str.format(
                "{schema}://{registry_host}{registry_port}/v2",
                schema="https" if registry_secure else "http",
                registry_host=registry_host,
                registry_port="" if not registry_port else ":"
                                                           + str(registry_port)
            )
        )
        self.catalog = None
        self.tags = {}
        self.manifests = []
        self._load_info()

    def _load_info(self):
        """
        Loads the information about the registry to refer later.
        """
        # Get the catalog
        catalog_url = self._registry_url + "/_catalog"
        tags_info = "/tags/list"
        c = request_url(catalog_url)
        if c:
            self.catalog = json.load(c)["repositories"]
        else:
            raise Exception("Could not get registry catalog.")
        for item in self.catalog:
            tags_url = self._registry_url + "/" + item + tags_info
            tags_data = request_url(tags_url)
            if tags_data:
                self.tags[item] = json.load(tags_data)


def delete_from_local_registry(container_namespace, container_name, container_tag):
    registry_storage_path = "/var/lib/registry/docker/registry/v2"
    registry_blobs = path.join(registry_storage_path, "blobs")
    registry_repositories = path.join(registry_storage_path, "repositories")
