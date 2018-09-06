from container_pipeline.lib.index import get_entries
from container_pipeline.cleanup_registry.registry import RegistryInfo
from container_pipeline.utils import get_gc_container_name


def _is_in_index(registry_entry, index_entries):
    for entry in index_entries:
        index_fullname = get_gc_container_name(entry.app_id, entry.job_id,
                                               entry.desired_tag)
        if index_fullname == registry_entry:
            return True

    return False


def diff(registry_url="", registry_port=None, registry_secure=False,
         index_path=""):
    diff_entries = {}
    index_entries = get_entries(index_path)
    registry_info = RegistryInfo(registry_url, registry_port, registry_secure)
    for registry_name, registry_tag_list in registry_info.tags.iteritems():
        registry_tags = registry_tag_list["tags"]
        if registry_tags:
            if registry_name not in diff_entries:
                diff_entries[registry_name] = []
            if registry_tags:
                for registry_tag in registry_tags:
                    if not _is_in_index(
                            str.format(
                                "{registry_name}:{registry_tag}",
                                registry_name=registry_name,
                                registry_tag=registry_tag
                            ),
                            index_entries
                    ):
                        diff_entries[registry_name].append(registry_tag)

    return diff_entries, index_entries, registry_info
