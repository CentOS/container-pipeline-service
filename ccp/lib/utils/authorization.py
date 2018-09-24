"""
This file contains authorization handlers
"""


class Authorization(object):

    def __init__(self):
        self.authorization_header_string = ""

    def add_header(self, headers):
        """
        Adds appropriate authorization headers to request headers
        :param headers: The headers dict
        :type headers dict
        """
        headers["Authorization"] = self.authorization_header_string


class BearerAuthorization(Authorization):

    def __init__(self, token):
        super(BearerAuthorization, self).__init__()
        self.authorization_header_string = "Bearer %s" % token
