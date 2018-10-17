"""
This file contains authorization handlers
"""


class Authorization(object):
    """
    Base class of authorizations. This class sets authorization classes
    """

    def __init__(self, authorization_header_string):
        """
        Initializes Authorization object, setting the authorization token
        :param authorization_header_string: The request header auth
        :type authorization_header_string: str
        """
        self.authorization_header_string = authorization_header_string

    def add_header(self, headers):
        """
        Adds appropriate authorization headers to request headers
        :param headers: The headers dict
        :type headers dict
        """
        headers["Authorization"] = self.authorization_header_string


class BearerAuthorization(Authorization):
    """
    Adds Bearer token based authorization header to request header
    """

    def __init__(self, token):
        """
        Sets the Bearer auth header based on token
        :param token: The authorization token
        :type token: str
        """
        super(BearerAuthorization, self).__init__(
            "Bearer %s" % token
        )
