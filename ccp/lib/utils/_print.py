"""
This library util module has _print method defined
which can be used to print messages on stdout realtime
and not being blocked on stdout buffer for showing the messages.
"""

import sys


def _print(msg):
    """
    _prints the given msg
    """
    print (msg)
    sys.stdout.flush()
