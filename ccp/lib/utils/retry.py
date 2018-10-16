"""
This library util module has retry decorator defined
which can be imported by other modules to have retry logic
implemented.
Reference implementation:
https://wiki.python.org/moin/PythonDecoratorLibrary#Retry
"""

import time
from functools import wraps

from ccp.lib.utils._print import _print


def retry(tries=10, delay=2, backoff=2):
    """
    Retry calling decorated function using an exponential backoff.

    :param tries: number of times to try before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    msg = "Error {0}, retrying in {1} seconds".format(
                        str(e), mdelay)
                    _print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    # (backoff * mdelay) seconds in next retry
                    mdelay *= backoff
            # executing as is after tries are lapsed
            return f(*args, **kwargs)
        return f_retry

    return deco_retry
