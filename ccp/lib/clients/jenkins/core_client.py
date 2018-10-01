"""
This file contains ready to use Jenkins Core Client.
"""

from ccp.lib.clients.jenkins.base import OpenshiftJenkinsBaseAPIClient, \
    jenkins_jobs_from_jobs_ordered_list


class OpenshiftJenkinsCoreAPIClient(OpenshiftJenkinsBaseAPIClient):
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
        Initialize Openshift Jenkins Client
        :param server: The URL/IP of jenkins server on openshift.
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
        super(OpenshiftJenkinsCoreAPIClient, self).__init__(
            server=server,
            secure=secure,
            verify_ssl=verify_ssl,
            token_from_mount=token_from_mount,
            sa=sa,
            namespace=namespace
        )

    def get_build_info(self, job_ordered_list, build_number):
        """
        Queries jenkins server about the build and retrieves the information
        :param job_ordered_list: he ordered list of jobs, with parents,
        followed by children
        :type job_ordered_list list
        :param build_number: The number of the build, whose information is
        neded
        :type build_number str
        :return: The response from jenkins
        :raises Exception
        """
        return self._query(
            "{jobs}/{build_number}/api/json".format(
                jobs=jenkins_jobs_from_jobs_ordered_list(
                    job_ordered_list
                ),
                build_number=str(build_number)
            )
        )
