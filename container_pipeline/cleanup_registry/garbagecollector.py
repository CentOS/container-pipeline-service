from container_pipeline.lib.index_registry_diff import diff
import re
from glob import glob

import config
import lib
from container_pipeline.lib.registry import RegistryInfo
from container_pipeline.utils import BuildTracker


class GarbageCollector(object):
    """
    Matches index with registry and cleans up mismatched data from the registry.
    """

    def __init__(self, registry_host="127.0.0.1", registry_port="5000",
                 registry_secure=False, local_index=False, index_git=None,
                 index_location="./c_i", verbose=True, collect=True):
        """
        Initialize the garbage collector object.

        :param registry_host: The ip or host name of registry to query. Default
         is 127.0.0.1.
        :param registry_port: The port of the registry to query. Default is 5000
        :param registry_secure: Is the registry secure or insecure (https or
        http)
        :param local_index: Is the index to query locally available. This means
         no cloning.
        :param index_git: If the index is on a git repo, the url of that repo.
        :param index_location: The path where the index is available or needs to
         be cloned.
        :param verbose: If set then steps are displayed on screen as they
        happen.
        :param collect: If set. then the garbage collection takes place, else it
         does dry run.
        """

        self._verbose = verbose
        self._index_location = index_location
        self._collect = collect
        self._local_index = local_index
        self._index_git = index_git
        self._gc_exceptions = []
        self._gc_match_only = []
        self._registry_host = registry_host
        self._registry_port = registry_port
        self._registry_secure = registry_secure
        self._index_d_location = self._index_location + "/index.d"
        # Setup reg info object to query the registry and cache metadata.
        self._index_check = False
        self._mismatched = {}

    def _prep_index(self):
        """
        Prepares the container index, and queries the same.
        """
        index_preped = False
        if self._local_index:
            # If local index is set, check if index files are present at
            # expected location.
            if not lib.path.exists(self._index_location):
                raise Exception("Local index specified, but does not exist")
            index_preped = True
        elif self._index_git:
            # Otherwise check if index git is specified, if so clone it.
            lib.print_msg("Cloning container index...", self._verbose)
            lib.clone_repo(self._index_git, self._index_location)
            index_preped = True

        return index_preped

    def _prep_lists(self):
        """
        Prepares the exceptions and matches list
        """

        if len(config.EXCEPTION_LIST) > 0:
            for exp in config.EXCEPTION_LIST:
                self._gc_exceptions.append(
                    re.compile(exp)
                )

        if len(config.MATCH_LIST) > 0:
            for exp in config.MATCH_LIST:
                self._gc_match_only.append(
                    re.compile(exp)
                )

    def _mark_for_removal(self):
        """Orphans mismatched images from registry."""
        lib.print_msg("Marking mismatched containers for removal...",
                      self._verbose)
        registry_storage_path = "/var/lib/registry/docker/registry/v2"
        registry_blobs = registry_storage_path + "/blobs"
        registry_repositories = registry_storage_path + "/repositories"
        for container_full_name, tag_list in self._mismatched.iteritems():
            # For every entry in mismatched, if a build is not currently running
            # remove it
            ## Formulate necessary data
            namespace = container_full_name.split("/")[0] \
                if "/" in container_full_name else container_full_name
            namespace_path = registry_repositories + "/" + namespace
            container_name = registry_repositories + "/" + container_full_name
            manifests = container_name + "/_manifests"
            tags = manifests + "/tags"
            # Delete the tag
            for item in tag_list:
                container_tag = str.format(
                    "{container_name}/{container_tag}",
                    container_name=container_full_name,
                    container_tag=item
                )
                if not BuildTracker(container_tag).is_running():
                    del_tag = tags + "/" + item
                    lib.rm(del_tag)

    def _delete_from_registry(self):
        """
        Deletes marked images from registry by invoking inbuild docker
        distribution gc.
        """
        cmd = [
            "registry",
            "garbage-collect",
            "/etc/docker-distribution/registry/config.yml"
        ]
        lib.run_cmd(cmd, no_shell=not self._verbose)

    def _gcollect(self):
        """Deletes the mismatched images from registry."""
        self._mark_for_removal()
        self._delete_from_registry()

    def _add_mismatched(self, k, v):
        """
        Adds the passed k and v to mismatched list.
        :param k: The k, which will be the container name
        :param v: The value, which will be the container tag
        """
        self._mismatched[k].append(v)

    def _update_mismatched(self, k, v, match=False,
                           match_found=False, exceptions=False,
                           exception_found=False):
        """
        Update mismatched entries, deciding if k, and v passed,
        need to be added to mismatched list, based on conditions
        :param k: The k, which will be the container name
        :param v: The value, which will be the container tag
        :param match: If true, it means match exception needs to be checked
        :param match_found: If true, it means k,v were found in match list.
        :param exceptions: If true, it means k, v were found in exception list,
        :param exception_found: If true, it means k,v was found in exception
        list
        """
        # initialize mismatched list, if not already initialized by adding k.
        if k not in self._mismatched:
            self._mismatched[k] = []
        # If matched and not in exceptions, then add to v to mismatched.
        if match and match_found:
            if not (exceptions and exception_found):
                self._add_mismatched(k, v)
        # If no match needed, still check for exception list and then add
        # to mismatched.
        elif not (exceptions and exception_found):
            self._add_mismatched(k, v)

    def _identify_mismatched(self):
        """
        Identify's images to be removed, by looking at registry, index, and any
        exceptions / match lists
        Note: Match list takes priority over exception list.
        """
        exception_list_check = True if len(self._gc_exceptions) > 0 else False
        match_only_check = True if len(self._gc_match_only) > 0 else False

        if self._index_check:
            diff_entries, _, _ = diff(
                self._registry_host,
                self._registry_port,
                self._registry_secure,
                self._index_location
            )
            for k, v in diff_entries.iteritems():
                for item in v:
                    match_only_list_found = False
                    exception_list_found = False
                    image_name = str.format(
                        "{name}:{tag}",
                        name=k,
                        tag=item
                    )
                    if match_only_check:
                        for exp in self._gc_match_only:
                            if exp.match(image_name):
                                match_only_list_found = True
                                break
                    if exception_list_check:
                        for exp in self._gc_exceptions:
                            if exp.match(image_name):
                                exception_list_found = True
                                break

                    self._update_mismatched(
                        k, item, match_only_check,
                        match_only_list_found, exception_list_check,
                        exception_list_found
                    )

        else:
            registry_info = RegistryInfo(
                registry_host=self._registry_host,
                registry_port=self._registry_port,
                registry_secure=self._registry_secure
            )
            for registry_name, registry_tags in registry_info.tags.iteritems():
                if registry_tags:
                    for tag in registry_tags:
                        match_only_list_found = False
                        exception_list_found = False
                        image_name = str.format(
                            "{name}:{tag}",
                            name=registry_name,
                            tag=tag
                        )
                        if match_only_check:
                            for exp in self._gc_match_only:
                                if exp.match(image_name):
                                    match_only_list_found = True
                                    break
                        if exception_list_check:
                            for exp in self._gc_exceptions:
                                if exp.match(image_name):
                                    exception_list_found = True
                                    break
                        self._update_mismatched(
                            registry_name, tag, match_only_check,
                            match_only_list_found, exception_list_check,
                            exception_list_found
                        )

    def run(self):
        """Initiate the garbage collection."""

        self._prep_lists()
        self._index_check = self._prep_index()
        self._identify_mismatched()

        end_msg = "Images to Remove"
        if self._collect:
            end_msg = "Images Removed"
            self._gcollect()
        print str.format("{0} : \n{1}", end_msg, self._mismatched)
