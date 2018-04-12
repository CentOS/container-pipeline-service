import re

from container_pipeline.lib import dj
from container_pipeline.cleanup_registry import lib, config
from container_pipeline.cleanup_registry.garbagecollector import \
    RegistryGarbageCollector
from container_pipeline.cleanup_registry.index_registry_diff import diff
from container_pipeline.models.pipeline import Build, Project


class PipelineRegistryGarbageCollector(RegistryGarbageCollector):
    """
    Matches index with registry and cleans up mismatched data from the registry
    """

    def __init__(self, registry_host="127.0.0.1", registry_port="5000",
                 registry_secure=False, local_index=False, index_git=None,
                 index_location="./c_i", verbose=True, collect=True):
        """
        Initialize the garbage collector object.

        :param registry_host: The ip or host name of registry to query. Default
         is 127.0.0.1.
        :param registry_port: The port of the registry to query. Default
         is 5000
        :param registry_secure: Is the registry secure or insecure (https or
        http)
        :param local_index: Is the index to query locally available. This means
         no cloning.
        :param index_git: If the index is on a git repo, the url of that repo.
        :param index_location: The path where the index is available or needs
         to be cloned.
        :param verbose: If set then steps are displayed on screen as they
        happen.
        :param collect: If set. then the garbage collection takes place, else
         it does dry run.
        """

        super(PipelineRegistryGarbageCollector, self).__init__(
            registry_host=registry_host,
            registry_port=registry_port,
            registry_secure=registry_secure,
            verbose=verbose,
            g_collect=collect,
            delete_revisions=True
        )
        self.index_location = index_location
        self.local_index = local_index
        self.index_git = index_git
        self.index_d_location = self.index_location + "/index.d"
        # Setup reg info object to query the registry and cache metadata.
        self.index_check = False

    def prep_index(self):
        """
        Prepares the container index, and queries the same.
        """
        index_preped = False
        if self.local_index:
            # If local index is set, check if index files are present at
            # expected location.
            if not lib.path.exists(self.index_location):
                raise Exception("Local index specified, but does not exist")
            index_preped = True
        elif self.index_git:
            # Otherwise check if index git is specified, if so clone it.
            lib.print_msg("Cloning container index...", self.verbose)
            lib.clone_repo(self.index_git, self.index_location)
            index_preped = True

        return index_preped

    def prep_lists(self):
        """
        Prepares the exceptions and matches list
        """

        if len(config.EXCEPTION_LIST) > 0:
            for exp in config.EXCEPTION_LIST:
                self.gc_exceptions.append(
                    re.compile(exp)
                )

        if len(config.MATCH_LIST) > 0:
            for exp in config.MATCH_LIST:
                self.gc_match_only.append(
                    re.compile(exp)
                )

    def identify_mismatched(self):
        """
        Identify's images to be removed, by looking at registry, index, and any
        exceptions / match lists
        Note: Match list takes priority over exception list.
        """
        exception_list_check = True if len(self.gc_exceptions) > 0 else False
        match_only_check = True if len(self.gc_match_only) > 0 else False

        if self.index_check:
            diff_entries, _, _ = diff(
                self.registry_host,
                self.registry_port,
                self.registry_secure,
                self.index_location
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
                        for exp in self.gc_match_only:
                            if exp.match(image_name):
                                match_only_list_found = True
                                break
                    if exception_list_check:
                        for exp in self.gc_exceptions:
                            if exp.match(image_name):
                                exception_list_found = True
                                break

                    self.update_mismatched(
                        k, item, match_only_check,
                        match_only_list_found, exception_list_check,
                        exception_list_found,
                        not self.check_build_running(
                            k, item
                        )
                    )

        else:
            for registry_name, registry_tags in self.registry_info.tags.\
                    iteritems():
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
                            for exp in self.gc_match_only:
                                if exp.match(image_name):
                                    match_only_list_found = True
                                    break
                        if exception_list_check:
                            for exp in self.gc_exceptions:
                                if exp.match(image_name):
                                    exception_list_found = True
                                    break
                        self.update_mismatched(
                            registry_name, tag, match_only_check,
                            match_only_list_found, exception_list_check,
                            exception_list_found,
                            not self.check_build_running(
                                registry_name,
                                tag
                            )
                        )

    @staticmethod
    def check_build_running(container_name, tag):
        entered_loop = False
        p_name = str.format(
            "{namespace}-{name}",
            namespace=container_name.split("/")[0] if "/" in container_name
            else "library",
            name=container_name.split("/")[1] if "/" in container_name
            else container_name
        )
        building_projects = Build.objects.filter(
            project__in=Project.objects.filter(
                name__icontains=p_name
            ),
            status__iregex=r'^((?!failed|error|complete).)*$'
        )

        for building_project in building_projects:
            entered_loop = True
            if building_project.test_tag and tag == building_project.test_tag:
                return True

        return entered_loop

    def pre_removal(self):
        self.prep_lists()
        self.index_check = self.prep_index()
        self.identify_mismatched()

    def post_removal(self):
        lib.print_msg("No post removal tasks", self.verbose)

