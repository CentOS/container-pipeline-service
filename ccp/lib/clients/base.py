from ccp.lib.utils.command import run_cmd2


class Client(object):
    """
    Base class for all clients
    """
    pass


class CmdClient(Client):
    """
    Base class for all Command Clients
    """

    def __init__(self, base_command):
        """
        Iniitalize the Cmd Client
        :param base_command: The core command to be used by client
        :type base_command str
        """
        super(Client, self).__init__()
        self.base_command = base_command

    def run_command(self, cmd, shell=False):
        """
        Runs the specified command
        :param cmd: The command to execute
        :type cmd str
        :param shell: Default False: Enable advanced shell function, not
        recommended
        :type shell bool
        :return:The output of command
        :rtype str
        :raises Exception
        """
        out, err = run_cmd2(cmd, shell=shell)
        if err:
            raise Exception(err)
        return out


