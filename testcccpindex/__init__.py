from argparse import ArgumentParser
from sys import exit

from Engine import Engine
from NutsAndBolts import Logger


def initparser():
    """Initializes the parser for parsing arguments."""

    parser = ArgumentParser(description="This script checks for errors in cccp entries.")

    parser.add_argument("-i",
                        "--indexentry",
                        help="Checks a specific index entry.",
                        metavar='ID',
                        nargs=1,
                        action="append")

    parser.add_argument("-t",
                        "--testentry",
                        help="Checks a test entry, independent of index.",
                        metavar=('ID', 'APPID', 'JOBID', 'GITURL', 'GITPATH', 'GITBRANCH', 'NOTIFYEMAIL'),
                        nargs=7,
                        action="append")

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

    parser.add_argument("-c",
                        "--customindexfile",
                        help="Specify a custom index.yml file which is locally available",
                        metavar='INDEXPATH',
                        nargs=1,
                        action="store")

    parser.add_argument("-s", "--skippass2",
                        help="Set to skip the second pass, which validates the cccp.yml file as well.",
                        action="store_true")

    return parser


def mainfunc():
    engine = None
    skippass2 = False
    datadumpdirectory = None
    indexgit = None
    customindexfile = None
    indexentries = None
    testentries = None

    cmdargs = initparser().parse_args()

    if cmdargs.indexgiturl is not None and cmdargs.customindexfile is not None:
        Logger().log(Logger.error,
                     "indexgiturl and customindexfile are mutually exclusive. So please specify either one")
        exit(5)

    if cmdargs.indexgiturl is not None:
        indexgit = cmdargs.indexgiturl[0]

    if cmdargs.customindexfile is not None:
        customindexfile = cmdargs.customindexfile

    if cmdargs.skippass2 is not None:
        skippass2 = cmdargs.skippass2

    if cmdargs.datadumpdirectory is not None:
        datadumpdirectory = cmdargs.datadumpdirectory[0]

    if cmdargs.indexentry is not None:

        indexentries = []
        for item in cmdargs.indexentry:
            indexentries.append(int(item[0]))

    if cmdargs.testentry is not None:
        testentries = cmdargs.testentry

    engine = Engine(datadumpdirectory=datadumpdirectory, indexgit=indexgit, customindexfile=customindexfile,
                    skippass2=skippass2, specificindexentries=indexentries, testindexentries=testentries)

    if not engine.run():
        exit(1)

    return


if __name__ == '__main__':
    mainfunc()
