"""
This file contains basic processor to process OpenShift information
"""

from ccp.lib.processors.base import QueryProcessor
from ccp.lib.clients.openshift.client import OpenShiftCmdClient


class OpenShiftCommandProcessor(QueryProcessor):

    def __init__(
            self,
            openshift_insecure=True,
            openshift_ca_path=None,
            openshift_client_cert_path=None,
            openshift_client_key_path=None
    ):
        """
        :param openshift_insecure: Default True: If true, then connection is
        insecure even with https so certs verification is ignored
        :type openshift_insecure: bool
        :param openshift_ca_path: Default None: If set, this is used to verify
        certs, assuming insecure is False
        :type openshift_ca_path: str
        :param openshift_client_cert_path: Default None: If provided then client
        cert path is used.
        :type openshift_client_cert_path: str
        :param openshift_client_key_path: Default None: If provided, then client
        key path is used.
        :type openshift_client_key_path: str
        """
        self.oc_client = OpenShiftCmdClient(
            insecure=openshift_insecure,
            ca_path=openshift_ca_path,
            client_cert_path=openshift_client_cert_path,
            client_key_path=openshift_client_key_path
        )

    def get_namespaces(self):
        """
        Gets the list of OpenShift namespaces/projects
        OpenShift returns the values in UTF-8 encoded format
        we need to decode it before processing
        :return: List of namespaces
        :rtype list
        :raises Exception
        :raises subprocess.CalledProcessError
        :raises ccp.lib.exceptions.CommandOutputError
        """
        return self.oc_client.get_projects().decode('UTF-8').split('\n')[:-1]
