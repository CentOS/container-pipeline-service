from argparse import ArgumentParser

from Engine import Engine

from pprint import PrettyPrinter


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
                        "--list",
                        help="Specify to print failed list",
                        action="store_true")

    parser.add_argument("-c",
                        "--cleanup",
                        help="Specify to force cleanup of test bench. If your running multiple times on same system,"
                             " this is not recommended as it will require downloading of repos again and again",
                        action="store_true")

    return parser


if __name__ == '__main__':

    cmd_args = get_parser().parse_args()
    indexd_location = "./index.d"
    data_dump_directory = "./cccp-index-test"
    clean_up = False

    if cmd_args.dump_directory is not None:
        data_dump_directory = cmd_args.dump_directory[0]

    if cmd_args.indexd_location is not None:
        indexd_location = cmd_args.indexd_location[0]

    if cmd_args.cleanup is not None and cmd_args.cleanup:
        clean_up = True

    print indexd_location

    e = Engine(indexd_location=indexd_location, data_dump_directory=data_dump_directory, cleanup=clean_up)
    status, status_list = e.run()

    if cmd_args.list is not None and cmd_args.list:
        for item in status_list:
            print item

    if not status:
        exit(1)
