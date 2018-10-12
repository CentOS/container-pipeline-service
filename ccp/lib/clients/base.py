from ccp.lib.utils.command import run_command


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
