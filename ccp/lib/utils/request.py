"""
This file handles API requests and returns the response for given API URL along
with provided parameters.
"""
import requests


def request_url(
        request, params=None, verify_ssl=False, auth=None, headers=None,
        timeout=5.0
):
    """
    Queries a specified URL and returns data, if any
    :param request: The url to send the request to.
    :type request: str
    :param params: Any params that are to be passed on to the request
    :type params: dict
    :param verify_ssl: IF False, ssl errors are ignored.
    :type verify_ssl: bool
    :param auth: This will be passed along to requests as is. Note: Passing
    auth overrides any Authorization headers passed already.
    :type auth dict
    :param headers: Any extra headers that you wish to pass along.
    :type headers: dict
    :param timeout: Default 5.0: The timeout, in seconds for a request to be
    processed
    :type timeout: float
    :raises requests.exceptions.RequestException
    :raises Exception
    :return: The response object, or None upon failure, if any or None
    """

    response = requests.get(
        request, params=params, verify=verify_ssl, headers=headers,
        auth=auth, timeout=timeout
    )

    return response
