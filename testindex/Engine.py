from IndexEntriesVerifier import IndexEntriesVerifier
from IndexVerifier import IndexVerifier
from NutsAndBolts import Logger
from NutsAndBolts import StaticHandler
from Globals import Globals


class Engine:
    """The engine, runs the vehicle ;)"""

    def __init__(self, datadumpdirectory=None, indexgit=None, custom_index_file=None, skippass2=False,
                 indexgitbranch="master"):
        """Initialize the engine, so it knows what to do."""

        # Initialze the engine
        StaticHandler.initialize(data_dump_directory=datadumpdirectory, index_git=indexgit, custom_index_location=custom_index_file
                                 , index_git_branch=indexgitbranch)

        # Setup engine started so its behavior is affected when it is started
        self._skipPass2 = skippass2

        return

    def _pass1(self):
        """Runs the first pass, and returns its success or failure"""

        return IndexVerifier().run()

    def _pass2(self):
        """Runs the second pass, and returns its success or failure"""

        return IndexEntriesVerifier().run()

    def run(self):
        """Ingition to the engine, this is what does the magic, and returns status of success or failure"""

        success = True
        l = Logger()

        l.log(Logger.info, "Starting the first pass...")

        # Run the first Pass
        pass1 = self._pass1()

        # Run the second pass if pass 1 passed and pass is not set to be skipped.
        if pass1 and not self._skipPass2:

            l.log(Logger.info, "Starting the second pass")
            success = self._pass2()

        else:

            success = pass1

        Logger().log(Logger.info, "Cleaning up systems")
        StaticHandler.cleanup()

        Logger().log(Logger.info, "Operations completed, check the dump directory for more information.")

        return success
