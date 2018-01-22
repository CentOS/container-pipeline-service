import re
from glob import glob

import config
import lib
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
        # Formulate the registry url
        self._registry_url = str.format("{schema}://{host}{port}/v2",
                                        schema="https" if registry_secure else
                                        "http",
                                        host=registry_host,
                                        port="" if not registry_port else ":" +
                                                                          registry_port
                                        )
        self._index_d_location = self._index_location + "/index.d"
        # Setup reg info object to query the registry and cache metadata.
        self._index_containers = {}
        self._mismatched = {}

    def _query_registry(self):
        lib.print_msg("Gathering registry metadata...", self._verbose)
        self._registry_info = lib.RegistryInfo(self._registry_url)

    def _query_index(self):
        """
        Query a cloned or local container index.
        """
        index_files = glob(self._index_d_location + "/*.yml")
        for index_file in index_files:
            if "index_template" not in index_file:
                data = lib.load_yaml(index_file)
                if "Projects" not in data:
                    raise Exception("Invalid index file")
                for entry in data["Projects"]:
                    app_id = entry["app-id"]
                    job_id = entry["job-id"]
                    desired_tag = entry["desired-tag"]
                    container_name = str.format(
                        "{namespace}{name}",
                        namespace=(str(app_id) + "/") if str(app_id) !=
                                                         "library" else "",
                        name=str(job_id)
                    )
                    container_tag = container_name + ":" + str(desired_tag)
                    if container_name not in self._index_containers:
                        #
                        self._index_containers[container_name] = []
                        if not BuildTracker(container_tag).is_running():
                            self._index_containers[container_name].append(
                                desired_tag
                            )

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

        if index_preped:
            # If there is an index to query, query it and populate image list
            self._query_index()

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

    def _gcollect(self):
        """Deletes the mismatched images from registry."""
        lib.print_msg("Removing mismatched containers...", self._verbose)
        registry_storage_path = "/var/lib/registry/docker/registry/v2"
        registry_blobs = registry_storage_path + "/blobs"
        registry_repositories = registry_storage_path + "/repositories"
        for container_full_name, tag_list in self._mismatched.iteritems():
            # For every entry in mismatched
            ## Formulate nessasary data
            namespace = container_full_name.split("/")[0] \
                if "/" in container_full_name else container_full_name
            namespace_path = registry_repositories + "/" + namespace
            container_name = registry_repositories + "/" + container_full_name
            manifests = container_name + "/_manifests"
            tags = manifests + "/tags"
            # Delete the tag
            for item in tag_list:
                del_tag = tags + "/" + item
                lib.rm(del_tag)
            # If no more tags, delete namespace
            subs = glob(tags + "/*")
            if len(subs) <= 0:
                lib.rm(namespace_path)

    def _identify_mismatched(self):
        """
        Identify's images to be removed, by looking at registry, index, and any
        exceptions / match lists
        Note: Match list takes priority over exception list.
        :return:
        """
        # Check if we need to check, index, match list and exception list
        index_check = True if len(self._index_containers) > 0 else False
        exception_list_check = True if len(self._gc_exceptions) > 0 else False
        match_only_check = True if len(self._gc_match_only) > 0 else False

        # Go through every container name and tag info pulled from registry
        for registry_name, registry_info in \
                self._registry_info.tags.iteritems():
            registry_tags = registry_info["tags"]
            if registry_name not in self._mismatched:
                self._mismatched[registry_name] = []
                for registry_tag in registry_tags:
                    image_name = str.format(
                        "{name}:{tag}",
                        name=registry_name,
                        tag=registry_tag
                    )
                    # Assume nothing matched
                    index_mismatched = False
                    exception_list_found = False
                    match_only_list_found = False

                    # If index needs to be checked
                    if index_check:
                        index_tags_list = self._index_containers.get(
                            registry_name
                        )
                        # If there are no tags in index to match with or
                        # registry tag not in the index, then its mismatch.
                        if not index_tags_list or (
                                index_tags_list and registry_tag not in
                                index_tags_list):
                            index_mismatched = True

                    # If we need to check the exception list
                    if exception_list_check:
                        for exp in self._gc_exceptions:
                            if exp.match(image_name):
                                exception_list_found = True
                                break

                    # If we need to check match only list
                    if match_only_check:
                        for exp in self._gc_match_only:
                            if exp.match(image_name):
                                match_only_list_found = True
                                break

                    # Do the actual matching now
                    if index_check:
                        if match_only_list_found and index_mismatched and not \
                                exception_list_found:
                            self._mismatched[registry_name].append(registry_tag)
                    else:
                        if match_only_list_found and not exception_list_found:
                            self._mismatched[registry_name].append(registry_tag)

    def run(self):
        """Initiate the garbage collection."""

        self._prep_lists()
        self._query_registry()
        self._prep_index()
        self._identify_mismatched()

        end_msg = "Images to Remove"
        if self._collect:
            end_msg = "Images Removed"
            self._gcollect()
        print str.format("{0} : \n{1}", end_msg, self._mismatched)
