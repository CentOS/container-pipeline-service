from glob import glob

import lib
from container_pipeline.utils import BuildTracker


class GarbageCollector(object):
    """
    Matches index with registry and cleans up mismatched data from the registry.
    """

    def __init__(self, registry_host="127.0.0.1", registry_port="5000", registry_secure=False, local_index=False,
                 index_git="https://github.com/centos/container-index", verbose=True, collect=True):
        """
        Initialize the garbage collector object.

        :param registry_host: The ip or host name of registry to query. Default is 127.0.0.1.
        :param registry_port: The port of the registry to query. Default is 5000
        :param registry_secure: Is the registry secure or insecure (https or http)
        :param local_index: Is the index to query locally available.
        :param index_git: If the index is on a git repo, the url of that repo.
        :param verbose: If set then steps are displayed on screen as they happen.
        :param collect: If set. then the garbage collection takes place, else it does dry run.
        """
        self._verbose = verbose
        self._index_location = "./c_i"
        self._collect = collect
        if local_index:
            # If local index is set, check if inex files are present at expected location.
            if not lib.path.exists(self._index_location):
                raise Exception("Local index specified, but does not exist")
        else:
            # Otherwise clone index.
            if self._verbose:
                print("Cloning container index...")
            lib.clone_repo(index_git, self._index_location)
        self._index_git = index_git
        # Formulate the registry url
        self._registry_url = str.format("{schema}://{host}{port}/v2",
                                        schema="https" if registry_secure else "http",
                                        host=registry_host,
                                        port="" if not registry_port else ":" + registry_port
                                        )
        self._index_location = self._index_location + "/index.d"
        # Setup reg info object to query the registry and cache metadata.
        if self._verbose:
            print("Gathering registry metadata...")
        self._registry_info = lib.RegistryInfo(self._registry_url)
        self.index_containers = {}
        self.mismatched = {}

    def _delete_mismatched(self):
        """Deletes the mismatched images from registry."""
        if self._verbose:
            print("Removing mismatched containers...")
        registry_storage_path = "/var/lib/registry/docker/registry/v2"
        registry_blobs = registry_storage_path + "/blobs"
        registry_repositories = registry_storage_path + "/repositories"
        for container_full_name, tag_list in self.mismatched.iteritems():
            # For every entry in mismatched
            ## Formulate nessasary data
            namespace = container_full_name.split("/")[0] if "/" in container_full_name else container_full_name
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

    def collect(self):
        """Initiate the garbage collection."""
        index_files = glob(self._index_location + "/*.yml")
        # Go through index files
        if self._verbose:
            print ("Going through the index.")
        for index_file in index_files:
            if "index_template" not in index_file:
                data = lib.load_yaml(index_file)
                if "Projects" not in data:
                    raise Exception("Invalid index file")
                for entry in data["Projects"]:
                    app_id = entry["app-id"]
                    job_id = entry["job-id"]
                    desired_tag = entry["desired-tag"]
                    # Initialize mismatch list to recieve data
                    container_name = str.format(
                        "{namespace}{name}",
                        namespace=(str(app_id) + "/") if str(app_id) != "library" else "",
                        name=str(job_id)
                    )
                    container_tag = container_name + ":" + str(desired_tag)
                    if container_name not in self.index_containers:
                        #
                        self.index_containers[container_name] = []
                    if not BuildTracker(container_tag).is_running():
                        self.index_containers[container_name].append(desired_tag)
        # Match index data with registry metadata
        for r_name, r_info in self._registry_info.tags.iteritems():
            r_tags = r_info["tags"]
            if r_name not in self.mismatched:
                self.mismatched[r_name] = []
            for item1 in r_tags:
                # On mismatch add to list
                if r_name in self.index_containers and item1 not in self.index_containers[r_name]:
                    self.mismatched[r_name].append(item1)
                if r_name not in self.index_containers:
                    self.mismatched[r_name].append(item1)
        end_msg = "Images to Remove"
        if self._collect:
            end_msg = "Images Removed"
            self._delete_mismatched()
        print str.format("{0} : \n{1}", end_msg, self.mismatched)
