from container_pipeline.cleanup_registry.registry import \
    mark_removal_from_local_registry, RegistryInfo, \
    delete_revision_tags_from_local, delete_from_registry

import lib


class RegistryGarbageCollector(object):

    def __init__(self, to_remove=None, registry_host="127.0.0.1",
                 registry_port="5000", registry_secure=False, verbose=True,
                 g_collect=True, delete_revisions=True, gc_exceptions=None,
                 gc_match=None):
        self.verbose = verbose
        self.registry_host = registry_host
        self.registry_port = registry_port
        self.registry_secure = registry_secure
        self.g_collect = g_collect
        self.delete_revisions = delete_revisions

        self.to_remove = {} if not to_remove else to_remove

        self.gc_exceptions = gc_exceptions if gc_exceptions else []
        self.gc_match_only = gc_match if gc_match else []
        self.registry_info = None
        self.load_registry_info()

    def load_registry_info(self):
        self.registry_info = RegistryInfo(
            registry_host=self.registry_host,
            registry_port=self.registry_port,
            registry_secure=self.registry_secure
        )

    def pre_removal(self):
        raise NotImplementedError

    def post_removal(self):
        raise NotImplementedError

    def mark_for_removal(self):
        lib.print_msg("Marking mismatched containers for removal...",
                      self.verbose)
        for container_full_name, tag_list in self.to_remove:
            for tag, remove in tag_list.iteritems():
                if "/" in container_full_name:
                    container_namespace, container_name = \
                        container_full_name.split("/")
                else:
                    container_namespace = None
                    container_name = container_full_name
                mark_removal_from_local_registry(
                    self.verbose,
                    container_namespace,
                    container_name,
                    tag,
                    remove
                )

    def set_mismatched(self, container_name, tag, remove=True):

        c = self.to_remove.get(container_name)
        if c:
            c[tag] = remove
        else:
            self.to_remove[container_name] = {
                tag: remove
            }

    def update_mismatched(self, container_name, container_tag,
                          match_only_check, matched, exception_list_check, ex,
                          remove=True):

        if match_only_check and matched:
            if not (exception_list_check and ex):
                self.set_mismatched(container_name, container_tag, remove)
        elif not (exception_list_check and ex):
            self.set_mismatched(container_name, container_tag, remove)

    def collect(self):
        lib.print_msg("Performing pre-garbage collection ops", self.verbose)
        self.pre_removal()
        lib.print_msg(
            str.format(
                "Images that will be removed : \n {}", str(self.to_remove)
            ),
            self.verbose
        )
        if self.g_collect:
            lib.print_msg("Cleaning up images...", self.verbose)
            self.mark_for_removal()
            self.cleanup()

        lib.print_msg("Performing post-garbage collection ops", self.verbose)
        self.post_removal()

    def cleanup(self):
        if self.delete_revisions:
            delete_revision_tags_from_local()
        delete_from_registry(self.verbose)
