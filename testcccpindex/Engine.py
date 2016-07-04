from IndexEntriesVerifier import IndexEntriesVerifier
from IndexVerifier import IndexVerifier
from NutsAndBolts import Logger
from NutsAndBolts import StaticHandler


class Engine:
    def __init__(self, datadumpdirectory=None, indexgit=None, customindexfile=None, skippass2=False,
                 specificindexentries=None, testindexentries=None):

        # Initialze the engine
        StaticHandler.initialize(datadumpdirectory, indexgit, customindexfile)

        # Setup engine starte so its behavior is affected when it is started
        self._skipPass2 = skippass2
        self._specificIndexEntries = specificindexentries
        self._testIndexEntries = testindexentries

        return

    def _pass1(self):

        return IndexVerifier().run()

    def _pass2(self):

        return IndexEntriesVerifier(self._specificIndexEntries, self._testIndexEntries).run()

    def run(self):

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

        Logger().log(Logger.info, "Operations completed, check the dump directory for more information.")

        return success
