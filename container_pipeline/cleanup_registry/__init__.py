import argparse

from garbagecollector import GarbageCollector


def get_args_parser():
    parser = argparse.ArgumentParser(
        description="Collect the images that do not match the index."
    )
    parser.add_argument(
        "-r",
        "--registryhost",
        help="The ip or hostname of registry to query.",
        metavar="REGISTRY_HOST",
        default="127.0.0.1"
    )
    parser.add_argument(
        "-p",
        "--registryport",
        help="The port of the registry to query",
        metavar="REGISTRY_PORT",
        default="5000"
    )
    parser.add_argument(
        "-s",
        "--secure",
        help="Set if the registry talks over https",
        action="store_true"
    )
    parser.add_argument(
        "--indexlocation",
        help="Specify location where you want to either clone index, or where"
             " you have already cloned it. Defaults to ./c_i",
        default="./c_i"
    )
    parser.add_argument(
        "-l",
        "--localindex",
        help="Set if you want to use locally available index. Note the index.d "
             "should be in index location",
        action="store_true"
    )
    parser.add_argument(
        "-i",
        "--indexgiturl",
        help="Specify the index git url to clone. If it is not specified, then "
             "no repo will be cloned.",
        default=None
    )
    parser.add_argument(
        "-c",
        "--collect",
        help="Enable this to make garbage collection work. Otherwise, it does a"
             " dry run",
        action="store_true"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Enable verbose for detailed messages",
        action="store_true"
    )

    return parser


def main():
    parser = get_args_parser().parse_args()

    registry_host = parser.registryhost
    registry_port = parser.registryport
    registry_secure = True if parser.secure else False
    index_location = parser.indexlocation
    local_index = True if parser.localindex else False
    index_git_url = parser.indexgiturl
    collect = True if parser.collect else False
    verbose = True if parser.verbose else False
    GarbageCollector(
        registry_host=registry_host,
        registry_port=registry_port,
        registry_secure=registry_secure,
        index_git=index_git_url,
        index_location=index_location,
        local_index=local_index,
        collect=collect,
        verbose=verbose
    ).run()


if __name__ == '__main__':
    main()
