from container_pipeline.utils import request_url, rm, print_msg, run_cmd
import json
from os import path
from time import sleep

REGISTRY_STORAGE_PATH = "/var/lib/registry/docker/registry/v2"
REGISTRY_REPOSITORIES = REGISTRY_STORAGE_PATH + "/repositories"
MANIFESTS = "/_manifests"
TAGS = "/tags"


class RegistryInfo(object):
    """Stores/Caches metadata from specified registry"""

    def __init__(self, registry_host, registry_port, registry_secure,
                 page_size=50):
        self._registry_url = str.format(
            str.format(
                "{schema}://{registry_host}{registry_port}",
                schema="https" if registry_secure else "http",
                registry_host=registry_host,
                registry_port="" if not registry_port else ":" +
                str(registry_port)
            )
        )
        self.catalog = None
        self.tags = {}
        self.manifests = []
        self._page_size = page_size
        self._load_info()

    def _load_catalog(self):
        """
        Loads the registry catalog.
        """
        self.catalog = []
        catalog_url = str.format(
            "{}/v2/_catalog?n={}",
            self._registry_url,
            str(self._page_size)
        )

        while True:
            c = request_url(catalog_url)
            if c:
                self.catalog = self.catalog + json.load(c)["repositories"]

            else:
                raise Exception("Could not get registry catalog.")

            nxt_page_link = c.headers.get('Link')
            if not nxt_page_link:
                break

            nxt_page = nxt_page_link.split(';')[0].strip('<>')
            catalog_url = str.format(
                "{}{}",
                self._registry_url,
                nxt_page
            )
            sleep(10)

    def _load_tags(self):
        tags_info = "/tags/list"
        for item in self.catalog:
            tags_url = str.format(
                "{}/v2/{}/{}",
                self._registry_url,
                item,
                tags_info
            )
            tags_data = request_url(tags_url)
            if tags_data:
                self.tags[item] = json.load(tags_data)

    def _load_info(self):
        """
        Loads the information about the registry to refer later.
        """
        # Get the catalog
        self._load_catalog()
        # Get the tags
        self._load_tags()


def delete_revision_tags_from_local():
    del_script = str.format(
        "{}/shell/registry_delete_revision_tags.sh",
        path.dirname(path.realpath(__file__))
    )
    cmd = ["/bin/bash", del_script]
    run_cmd(cmd, check_call=False, wait_for_completion=True)


def mark_removal_from_local_registry(verbose, container_namespace,
                                     container_name, container_tag,
                                     delete=True):
    print_msg(
        str.format(
            "Marking {}{}:{} mismatched container for removal ...",
            str(container_namespace) + "/" if container_namespace else "",
            container_name,
            container_tag
        ),
        verbose
    )

    if container_namespace:
        namespace_path = path.join(REGISTRY_REPOSITORIES, container_namespace)
    else:
        namespace_path = REGISTRY_REPOSITORIES
    name_path = path.join(namespace_path, container_name)
    manifests = name_path + MANIFESTS
    tags = manifests + TAGS
    # Delete the tag
    if delete:
        del_tag = path.join(tags, container_tag)
        rm(del_tag)


def delete_from_registry(verbose,
                         config="/etc/docker-distribution/registry/config.yml"
                         ):
    """
    Deletes marked images from registry by invoking inbuild docker
    distribution gc.
    """
    cmd = [
        "registry",
        "garbage-collect",
        config
    ]
    run_cmd(cmd, no_shell=not verbose)
