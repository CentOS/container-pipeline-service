from ccp.lib.clients.base import APIClient
from ccp.lib.clients.openshift.client import OpenShiftCmdClient
from ccp.lib.utils.authorization import Authorization, BearerAuthorization


def jenkins_jobs_from_jobs_ordered_list(nested_job_ordered_list):
    """
    Formats query part of URL from ordered job list as /job/j1/job/j2
    :param nested_job_ordered_list: The ordered list of jenkins job names,
    with parent as first and every child below.
    :type nested_job_ordered_list list
    :return: A string of the form /job/j1/job/j2...
    """
    dest = ""
    for i in nested_job_ordered_list:
        dest = "{}/job/{}".format(
            dest,
            i
        )
    return dest


class OpenshiftJenkinsBaseAPIClient(APIClient):

    def __init__(
            self,
            server,
            secure=True,
            verify_ssl=True,
            token_from_mount=None,
            sa="sa/jenkins",
            namespace="default"
    ):
        """
        Initialize Jenkins APIClient
        :param server: The URL/IP server to hit.
        :type server str
        :param secure: Default True: Use SSL for queries.
        :type secure bool
        :param verify_ssl: Default True: Verify SSL certificate.
        :param token_from_mount: Default None: Set if you have token mounted
        at a path. Otherwise, ensure the openshift context is already set.
        :type token_from_mount str
        :param sa: Default 'sa/jenkins': Name of the service account whose
        token is to be used.
        :type sa str
        :param namespace: The namespace of the Jenkins secret, if not mounted
        :type namespace str
        """

        c = OpenShiftCmdClient()
        token = c.get_token_from_mounted_secret(token_from_mount)\
            if token_from_mount else c.get_sa_token_from_openshift(
            sa=sa, namespace=namespace
        )
        super(OpenshiftJenkinsBaseAPIClient, self).__init__(
            server=server,
            secure=secure,
            verify_ssl=verify_ssl,
            authorization=BearerAuthorization(token=token)
        )

