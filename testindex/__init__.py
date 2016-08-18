from argparse import ArgumentParser
from sys import exit

from Engine import Engine
from NutsAndBolts import Logger


def initparser():
    """Initializes the parser for parsing arguments."""

    parser = ArgumentParser(description="This script checks for errors in cccp entries.")

    parser.add_argument("-d",
                        "--datadumpdirectory",
                        help="Specify your own dump directory for test data such as index, repos and logs",
                        metavar="DUMPDIRPATH",
                        nargs=1,
                        action="store")

    parser.add_argument("-g",
                        "--indexgiturl",
                        help="Specify the giturl containing your index.yml",
                        metavar='GITURL',
                        nargs=1,
                        action="store")

    parser.add_argument("-b",
                        "--indexgitbranch",
                        help="Set if you want to the index to be from a branch other than master",
                        metavar="INDEXGITBRANCH",
                        nargs=1,
                        action="store")

    parser.add_argument("-c",
                        "--customindexfile",
                        help="Specify a custom index.d path which is locally available",
                        metavar='INDEXPATH',
                        nargs=1,
                        action="store")

    parser.add_argument("-s", "--skippass2",
                        help="Set to skip the second pass, which validates the cccp.yml file as well.",
                        action="store_true")

    return parser


def mainfunc():
    """The entry point. Note, if you want dont want argument parsing, feel free to directly use Engine class"""

    engine = None
    skippass2 = False
    datadumpdirectory = None
    indexgit = None
    customindexfile = None
    indexgitbranch = "master"

    cmdargs = initparser().parse_args()

    # Set up the parameters to Engine, based on argument parsing.

    if cmdargs.indexgiturl is not None:
        indexgit = cmdargs.indexgiturl[0]

    if cmdargs.indexgitbranch is not None:
        indexgitbranch = cmdargs.indexgitbranch[0]

    if cmdargs.customindexfile is not None:
        customindexfile = cmdargs.customindexfile[0]

    if cmdargs.skippass2 is not None:
        skippass2 = cmdargs.skippass2

    if cmdargs.datadumpdirectory is not None:
        datadumpdirectory = cmdargs.datadumpdirectory[0]

    engine = Engine(datadumpdirectory=datadumpdirectory, indexgit=indexgit, custom_index_file=customindexfile,
                    skippass2=skippass2, indexgitbranch=indexgitbranch)

    status = engine.run()

    if not status:
        exit(1)

    return


if __name__ == '__main__':
    mainfunc()
