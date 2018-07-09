import sys
from os import path

fl = path.dirname(path.realpath(__file__))
sys.path.append(path.join(fl, "..", ".."))

from argparse import ArgumentParser
import ci.container_index.engine as engine


def init_parser():
    parser = ArgumentParser(
        description="This tool lets you run index validations from the CLI"
    )
    parser.add_argument(
        "-i",
        "--index",
        help="Specify location of index. This is where index.d is Default .",
        metavar="INDEX_PATH",
        default="."
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Verbose mode prints more output of the tests",
        action="store_true"
    )

    return parser


def print_summary(index_ci_summary, report_verbose):
    if report_verbose:
        print(str.format(
            "\n{} Container Index CI Report {}\n\n",
            "*" * 5,
            "*" * 5
        ))
        for file_name, messages in index_ci_summary.iteritems():
            print(
                str.format(
                    "File Name : {}\n",
                    path.basename(file_name)
                )
            )
            for message in messages:
                print(
                    str.format(
                        "TITLE: {} \nDATA :\n {}\nSUCCESS : {}\n",
                        message.title,
                        message.data,
                        message.success,
                    )
                )
                if len(message.errors) > 0:
                    print("Errors : \n")
                    for err in message.errors:
                        print(
                            str.format(
                                " ERR - {}\n", err
                            )
                        )
                if len(message.warnings) > 0:
                    print("Warnings : \n")
                    for warn in message.warnings:
                        print(
                            str.format(
                                "WARN - {}\n", warn
                            )
                        )
                print("*" * 10)
                print("\n")
            print("*" * 20)
            print("\n")


def main():
    args = init_parser().parse_args()

    index = args.index
    verbose = True if args.verbose else False
    success, summary = engine.Engine(
        index_location=index,
        verbose=verbose
    ).run()
    print_summary(summary, verbose)
    if not success:
        exit(1)


main()
