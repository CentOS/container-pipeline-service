from argparse import ArgumentParser

from Engine import Engine


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

    parser.add_argument("-l",
                        "--list_failed",
                        help="Specify to print failed list",
                        action="store_true")

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
    status, failed_list = e.run()

    if not status:
        if cmd_args.list_failed is not None and cmd_args.list_failed:
            print failed_list
        exit(1)
