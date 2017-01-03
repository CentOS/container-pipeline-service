from argparse import ArgumentParser

from Engine import Engine


def get_parser():
    """Initializes and returns an argument parser object"""
    parser = ArgumentParser(description="This script is used to validate the contents on the index.d directory.")

    parser.add_argument(
        "-i",
        "--index",
        help="Specify location of index. Default is ./index.d",
        metavar="INDEX_PATH",
        default="./index.d"
    )

    parser.add_argument(
        "-c",
        "--cleanup",
        help="Specify to force cleanup of test bench. If your running multiple times on same system,"
        " this is not recommended as it will require downloading of repositories again and again",
        action="store_true"
    )

    return parser


if __name__ == '__main__':

    cmd_args = get_parser().parse_args()
    clean_up = False
    verbose = False

    index = cmd_args.index

    if cmd_args.cleanup:
        clean_up = True

    e = Engine(index_path=index, cleanup=clean_up, verbose=verbose)
    status, status_list, dependency_graph = e.run()
    status_data = {
        "status": status,
        "dependency_graph": {
            "nodes": dependency_graph.get_internal_graph().nodes(data=True),
            "edges": dependency_graph.get_internal_graph().edges(),
            "processing_order": dependency_graph.get_processing_order()
        }
    }

    print status_data
