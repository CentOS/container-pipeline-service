from Engine import Engine
from argparse import ArgumentParser


def get_parser():
    parser = ArgumentParser(description="This script is used to validate the contents on the index.d directory.")

    parser.add_argument("-d",
                        "--dump_directory",
                        help="Specify a custom data dump directory",
                        metavar='DUMPDIR',
                        nargs=1,
                        action="store")

    parser.add_argument("-i",
                        "--indexd_location",
                        help="Specify location of indexd. Default is ./index.d",
                        metavar="INDEXD",
                        nargs=1,
                        action="store")

    return parser


if __name__ == '__main__':

    cmd_args = get_parser().parse_args()
    indexd_location = "./index.d"
    data_dump_directory = "./cccp-index-test"

    if cmd_args.dump_directory is not None:
        data_dump_directory = cmd_args.dump_directory[0]

    if cmd_args.indexd_location is not None:
        indexd_location = cmd_args.indexd_location[0]

    print indexd_location

    e = Engine(indexd_location=indexd_location, data_dump_directory=data_dump_directory)
    status = e.run()

    if not status:
        exit(1)
