import networkx as nx


class ContainerDependencyGraph(object):
    """This class encapsulates a python-networkx Directed Graph which is used to maintain
    a dependency graph of containers"""

    def __init__(self):
        """Initializes an object of Container Dependency Graph"""
        # Networkx represents each node as a list whose 1st element is a number to uniquely identify the node, and
        # also help connect the edges, and the 2nd element is a dict which holds attributes which can be attached
        # to each node.
        self._dependency_graph = nx.DiGraph()
        self._node_number = 1

    def get_container_node(self, container_id=None, container_name=None):
        """Gets the node, identified by container_name from the graph, if it exists."""
        node = None
        # Get the nodes from the networkx graph to iterate through
        nodes = self._dependency_graph.nodes(data=True)
        # Check if we need to get node by id or by name
        # If neither is provided, raise exception
        if not container_id and not container_name:
            return None, "Either the id or the name of the container must be specified"
        elif not container_id and container_name:
            for item in nodes:
                # Check the name label associated with the node to check if its the container_name we are looking for
                if "name" in item[1] and container_name == item[1]["name"]:
                    node = item
                    break
        # else if container id is provided, we just ignore container name
        else:
            for item in nodes:
                # Check for matching id
                if container_id == item[0]:
                    node = item
                    break
        return node

    def add_container(self, container_name, from_index=False, from_target_file=False):
        """Checks if a node exists for container_name, and adds it if it does not exist
        container_name: Name of the container
        from_index: set to true, if the container was found in the container index
        from_target_file: set to true, if container was found in target-file
        """
        # Check if node already exists for container_name
        node = self.get_container_node(container_name=container_name)
        if not node:
            # If not, add a new node for the container_name
            self._dependency_graph.add_node(self._node_number, name=container_name, from_index=from_index,
                                            from_target_file=from_target_file)
            self._node_number += 1
        else:
            # Otherwise update the attributes of node to indicate from_index and from_target_file
            fi = node[1]["from_index"]
            ftb = node[1]["from_target_file"]
            # If from_index is false and we it is now being set to true
            if not fi and from_index:
                node[1]["from_index"] = True
            # If from_target_file is false and is now being set to true
            if not ftb and from_target_file:
                node[1]["from_target_file"] = True

    def add_dependency(self, from_container, to_container):
        """Add a dependency between the containers as a directed edge from one container to the other."""
        # Get the nodes for the containers specified
        from_node = self.get_container_node(container_name=from_container)
        to_node = self.get_container_node(container_name=to_container)
        err_names = []
        # Check if nodes are available for both the containers, if not then, they should have been added already
        if from_node and to_node:
            # Extract he numbers which uniquely identify the node, so that an edge can be formed between them,
            # if not already present
            f = from_node[0]
            t = to_node[0]
            # Get the edges from the graph and check is an edge does not already exist for the pair, if not add it now.
            edges = self._dependency_graph.edges()
            if (f, t) not in edges:
                self._dependency_graph.add_edge(f, t)
            return True
        else:
            if not from_node:
                err_names.append(from_container)
            if not to_node:
                err_names.append(to_container)
            return False, err_names

    def has_no_cycles(self):
        """Check that the dependency graph is acyclic"""
        return nx.is_directed_acyclic_graph(self._dependency_graph)

    def get_internal_graph(self):
        """Get the internal networkx graph"""
        return self._dependency_graph

    def dependency_exists(self, from_container, to_container):
        """Checks if a dependency exists from a container, to a container."""
        # Get the nodes for the containers specified
        from_node = self.get_container_node(container_name=from_container)
        to_node = self.get_container_node(container_name=to_container)
        # Check if nodes are available for both the containers, if not then, they should have been added already
        if from_node and to_node:
            # Extract he numbers which uniquely identify the node, so that an edge can be formed between them,
            # if not already present
            f = from_node[0]
            t = to_node[0]
            # Get the edges from the graph and check is an edge exist for the pair. If not, then no dependency
            edges = self._dependency_graph.edges()
            if (f, t) in edges:
                return True
        else:
            return False

    @staticmethod
    def _resolve_dependencies(dependencymap):
        """
            Dependency resolver
        "dependencymap" is a dependency dictionary in which
        the values are the dependencies of their respective keys.
        The function returns a list of sets, such that, elements
        of the set can be processed in parallel, but each set, must
        be processed, after its preceeding set.
        """
        d = dict((k, set(dependencymap[k])) for k in dependencymap)
        r = []

        while d:
            # values not in keys (items without dep)
            # Basically if an item x is in values, then it has another item y in the keys
            # which depends on x : x -> y , but if x is not in keys, then it does not have
            # anyone that it depends on
            t = set(i for v in d.values() for i in v) - set(d.keys())
            # and keys without value (items without dep)
            # Basically if an item x has no items in the values, then it does not have any item
            # that it depends on
            t.update(k for k, v in d.items() if not v)
            # can be done right away
            r.append(t)
            # and cleaned up
            # Here, read every key value pair in the dict, and process further if the v is not empty
            # (k has dependencies) So basically we only take those items forward that that dependencies
            # Create a new dict such that for every key, the value does not contain items that have been
            # added to t, as they are a part of that set.
            d = dict(((k, v - t) for k, v in d.items() if v))

        return r

    def get_processing_order(self):
        """Traverses the dependency graph and gets the order in which the nodes can be processed, as a list of lists."""
        # Create a dependency map by traversing the graph, see _resolve_dependencies for more information
        nodes = self._dependency_graph.nodes()
        edges = self._dependency_graph.edges()
        dependency_map = {}
        for node in nodes:
            # Add an entry in dependency map for the node
            dependency_map[node] = []
            # Check if there are any nodes that have an edge from them to current node respectively
            # This indicates dependency from any node to current node
            for edge in edges:
                if node == edge[1]:
                    # If so, record the dependency in the dependency map
                    dependency_map[node].append(edge[0])
        return ContainerDependencyGraph._resolve_dependencies(dependency_map)

    def get_cycles(self):
        """Returns a list of cycles in the dependency graph, if they are present."""
        cycles = None
        try:
            cycles = nx.find_cycle(self._dependency_graph)
        except Exception:
            pass
        return cycles


class DependencyValidator(object):
    """Does the container dependency validation."""

    def __init__(self):
        self.dependency_graph = ContainerDependencyGraph()

    def is_dependency_acyclic(self):
        """Check is the dependency graph is acyclic."""
        return self.dependency_graph.has_no_cycles()
