import requests


def request_url(
        request, params=None, verify_ssl=False, auth=None, headers=None
):
    """
    Queries a specified URL and returns data, if any
    :param request: The url to send the request to.
    :type request str
    :param params: Any params that are to be passed on to the request
    :type params dict
    :param verify_ssl: IF False, ssl errors are ignored.
    :type verify_ssl bool
    :param auth: This will be passed along to requests as is. Note: Passing
    auth overrides any Authorization headers passed already.
    :type auth dict
    :param headers: Any extra headers that you wish to pass along.
    :type headers dict
    :raises Exception
    :return: The response object, or None upon failure, if any or None
    """

    response = requests.get(
        request, params=params, verify=verify_ssl, headers=headers,
        auth=auth
    )

    return response
