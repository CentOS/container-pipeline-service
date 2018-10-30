"""
This library util module has _print method defined
which can be used to print messages on stdout realtime
and not being blocked on stdout buffer for showing the messages.
"""

import sys


def print_out(msg):
    """
    prints the given msg
    :param msg: What to print
    """
    print (msg)
    sys.stdout.flush()
