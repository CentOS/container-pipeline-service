"""
This file contains ready to use Jenkins workflow Client.
"""

from ccp.lib.clients.jenkins.base import OpenshiftJenkinsBaseAPIClient, \
    jenkins_jobs_from_jobs_ordered_list
from ccp.lib.utils.retry import retry


class OpenshiftJenkinsWorkflowAPIClient(OpenshiftJenkinsBaseAPIClient):
    """
    Helps query the jenkins workflow API endpoints.
    """

    def __init__(
            self,
            server,
            secure=True,
            verify_ssl=True,
            token=None,
            token_from_mount=None,
            sa="sa/jenkins",
            namespace="default"
    ):
        """
        Initialize Openshift Jenkins Client
        :param server: The URL/IP of jenkins server on openshift.
        :type server str
        :param secure: Default True: Use SSL for queries.
        :type secure bool
        :param verify_ssl: Default True: Verify SSL certificate.
        :param token: Default None: If provided then, this is set as the token
        to use to login to OpenShift. Overrides all other ways of providing
        token
        :type token str
        :param token_from_mount: Default None: Set if you have token mounted
        at a path. Otherwise, ensure the openshift context is already set.
        :type token_from_mount str
        :param sa: Default 'sa/jenkins': Name of the service account whose
        token is to be used.
        :type sa str
        :param namespace: The namespace of the Jenkins secret, if not mounted
        :type namespace str
        """
        super(OpenshiftJenkinsWorkflowAPIClient, self).__init__(
            server=server,
            secure=secure,
            verify_ssl=verify_ssl,
            token=token,
            token_from_mount=token_from_mount,
            sa=sa,
            namespace=namespace
        )

    @retry(tries=10, delay=2, backoff=2)
    def get_build_runs(self, job_ordered_list):
        """
        Gets the build runs of specified job/subjob from API server
        :param job_ordered_list: The ordered list of jobs, with parents,
        followed by children
        :type job_ordered_list list
        :raises Exception
        :return: The Response returned by API server, if it is received.
        """
        return self._query(
            "{}/wfapi/runs".format(
                jenkins_jobs_from_jobs_ordered_list(
                    job_ordered_list
                )
            )
        )

    @retry(tries=10, delay=2, backoff=2)
    def describe_build_run(self, job_ordered_list, build_number):
        """
        Describes a particular build run of job/subjob from API server
        :param job_ordered_list: The ordered list of jobs, with parents,
        followed by children
        :type job_ordered_list list
        :param build_number: The number of build to describe.
        :type build_number str
        :raises Exception
        :return: The Response returned by the API server, if it is received.
        """
        return self._query(
            "{}/{}/wfapi/describe".format(
                jenkins_jobs_from_jobs_ordered_list(
                    job_ordered_list
                ),
                build_number
            )
        )

    @retry(tries=10, delay=2, backoff=2)
    def describe_execution_node(
            self, job_ordered_list, build_number, node_number
    ):
        """
        Describes an execution node for job/subjob from API server
        :param job_ordered_list: The ordered list of jobs, with parents,
        followed by children
        :param build_number:The number of the build to describe.
        :param node_number: The number of the node to describe
        :raises Exception
        :return: The Response from the API server, if it is received.
        """
        return self._query(
            "{}/{}/execution/node/{}/wfapi/describe".format(
                jenkins_jobs_from_jobs_ordered_list(
                    job_ordered_list
                ),
                build_number,
                node_number
            )
        )

    @retry(tries=10, delay=2, backoff=2)
    def get_logs_of_execution_node(
            self, job_ordered_list, build_number, node_number
    ):
        """
        Lets the logs of a jenkins execution node, if possible
        :param job_ordered_list: The ordered list of jobs, with parents,
        followed by children
        :param build_number: The number of the build to describe.
        :param node_number: The number of the node to describe
        :raises Exception
        :return: The response from API server, if it is received.
        """
        return self._query(
            "{}/{}/execution/node/{}/wfapi/log".format(
                jenkins_jobs_from_jobs_ordered_list(
                    job_ordered_list
                ),
                build_number,
                node_number
            )
        )
