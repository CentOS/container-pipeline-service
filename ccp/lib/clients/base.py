from ccp.lib.utils.command import run_command
from ccp.lib.utils.request import request_url
from ccp.lib.utils.authorization import Authorization


class Client(object):
    """
    Base class for all clients
    """
    pass


class CmdClient(Client):
    """
    Base class for all Command Clients
    These clients execute commands on behalf of program and
    return any output for processing.
    """

    def __init__(self, base_command):
        """
        Iniitalize the Cmd Client
        :param base_command: The core command to be used by client
        :type base_command: str
        """
        super(Client, self).__init__()
        self.base_command = base_command


class APIClient(Client):
    """
    Base class for all clients that query an API Server for information
    """
    def __init__(
            self,
            server,
            secure=True,
            verify_ssl=True,
            authorization=None
    ):
        """
        Initialize APIClient
        :param server: The URL/IP server to hit.
        :type server str
        :param secure: Default True: Use SSL for queries.
        :type secure bool
        :param verify_ssl: Default True: Verify SSL certificate.
        :param authorization: Set if you want or need to use Authorization
        :type authorization Authorization
        """
        self.server_endpoint = "{}://{}".format(
            "https" if secure else "http",
            server if server else "localhost"
        )
        self.authorization = authorization
        self.skip_ssl = verify_ssl

    def _query(self, target, headers=None):
        """
        Given a target (query without url), queries endpoint and gets data
        :param target: The query to send to the api server, after the hostname
        and port. For eg: URL = http://example.com/hello, then target will be
        '/hello'
        :type target str
        :param headers: Any headers you wish to add to query.
        :type headers dict
        :return:The response object and exception object, if any was raised.
        """
        query_url = "{}{}".format(
            self.server_endpoint,
            target
        )
        request_headers = {}
        if self.authorization and isinstance(self.authorization, Authorization):
            self.authorization.add_header(request_headers)
        if headers and isinstance(headers, dict):
            request_headers.update(headers)
        return request_url(
            query_url, verify_ssl=self.skip_ssl, headers=request_headers
        )

