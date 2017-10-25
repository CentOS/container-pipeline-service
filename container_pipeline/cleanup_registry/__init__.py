from garbagecollector import GarbageCollector
import argparse


def get_args_parser():
    parser = argparse.ArgumentParser(description="Collect the images that do not match the index.")
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
        "-l",
        "--localindex",
        help="Set if you want to use locally available index. Note the index.d should be in ./c_i directory",
        action="store_true"
    )
    parser.add_argument(
        "-i",
        "--indexurl",
        help="The git url of index to be cloned.",
        default="https://github.com/centos/container-index"
    )
    parser.add_argument(
        "-d",
        "--dryrun",
        help="Enable this to do a dry run of the garbge collector without removing images",
        action="store_true"
    )

    return parser


def main():
    parser = get_args_parser().parse_args()

    registry_host = parser.registryhost
    registry_port = parser.registryport
    registry_secure = True if parser.secure else False
    local_index = True if parser.localindex else False
    index_url = parser.indexurl
    dry_run = True if parser.dryrun else False

    gc = GarbageCollector(registry_host=registry_host, registry_port=registry_port, registry_secure=registry_secure,
                          local_index=local_index, index_git=index_url, dry_run=dry_run)
    gc.collect()

if __name__ == '__main__':
    main()