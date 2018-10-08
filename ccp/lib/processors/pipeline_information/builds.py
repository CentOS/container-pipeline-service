"""
This file contains Jenkins query processors for build information
"""

from ccp.lib.clients.jenkins.core_client import OpenshiftJenkinsCoreAPIClient
from ccp.lib.clients.jenkins.workflow_client import \
    OpenshiftJenkinsWorkflowAPIClient
from ccp.lib.constants.jenkins import *
from ccp.lib.processors.base import JSONQueryProcessor


class OpenshiftJenkinsBuildInfo(JSONQueryProcessor):
    """
    This class processes queried information from jenkins
    for requested information.
    """
    def __init__(
            self, jenkins_server="localhost",
            verify_ssl=False,
            token=None,
            sa="sa/jenkins",
            namespace="default",
            token_from_mount=None,
            test=False
    ):
        """
        Initializes the BuildInfo to fetch processed build information.
        :param jenkins_server: The URL/IP of jenkins server on OpenShift.
        :type jenkins_server str
        :param verify_ssl: Default True: Verify SSL certificate.
        :type verify_ssl bool
        :param token: Default None: If provided then, this is set as the token
        to use to login to OpenShift. Overrides all other ways of providing
        token
        :type token str
        :param sa: Default 'sa/jenkins': Name of the service account whose
        token is to be used.
        :type sa str
        :param namespace: Default default : The namespace of the jenkins and
        builds.
        :type namespace str
        :param token_from_mount: Default None: Set if you have token mounted
        at a path. Otherwise, ensure the OpenShift context is already set.
        :type token_from_mount str
        :param test: Default False: Use only by tests. Instead of fetching data
        using the clients, data is expected to be provided and will only be
        parsed
        :type test bool
        :raises Exception
        """
        self.test = test
        if not test:
            self.jenkins_core_client = OpenshiftJenkinsCoreAPIClient(
                server=jenkins_server,
                verify_ssl=verify_ssl,
                token=token,
                sa=sa,
                namespace=namespace,
                token_from_mount=token_from_mount
            )
            self.jenkins_workflow_client = OpenshiftJenkinsWorkflowAPIClient(
                server=jenkins_server,
                verify_ssl=verify_ssl,
                token=token,
                sa=sa,
                namespace=namespace,
                token_from_mount=token_from_mount
            )

    def get_builds_count(self, ordered_job_list, test_data_set=None):
        """
        Get the count of build in the project. Helps indeciding id to query.
        :param ordered_job_list: The ordered list of jobs, with parents,
        followed by children
        :type ordered_job_list list
        :param test_data_set: data set to be used for test run.
        :type test_data_set list
        :return: A number representing number of builds in a job.This number
        will also be id of latest build. -1 is returned on failure.
        """
        if not self.test:
            data_set = self.get_data_from_response(
                self.jenkins_workflow_client.get_build_runs(ordered_job_list),
                bad_json=True
            )
        else:
            data_set = test_data_set
        if data_set:
            count = len(data_set)
        else:
            count = -1
        return count

    def get_build_status(
            self, ordered_job_list, build_number, test_data_set=None
    ):
        """
        Gets the overall status of a particular build
        :param ordered_job_list: The ordered list of jobs, with parents,
        followed by children
        :type ordered_job_list list
        :param build_number: The id of the build.
        :type build_number str
        :param test_data_set: data that is to be used for test run.
        :type test_data_set dict
        :return: The overall result of the build. None is returned on failure
        :raises Exception
        """
        result = None
        if not self.test:
            data_set = self.get_data_from_response(
                self.jenkins_core_client.get_build_info(
                    ordered_job_list, build_number
                )
            )
        else:
            data_set = test_data_set
        if data_set:
            result = data_set.get("result")
        return result

    def get_cause_of_build(
            self, ordered_job_list, build_number, test_data_set=None
    ):
        """
        Gets the cause of that triggered the build.
        :param ordered_job_list: The ordered list of jobs, with parents,
        followed by children
        :type ordered_job_list list
        :param build_number: The id of the build.
        :type build_number str
        :param test_data_set: ata that is to be used for test run.
        :type test_data_set dict
        :return: The cause that triggered the build. None is returned on
        failure
        :raises KeyError
        :raises Exception
        """
        result = {
            "cause": None
        }
        if not self.test:
            data_set = self.get_data_from_response(
                self.jenkins_core_client.get_build_info(
                    ordered_job_list, build_number
                )
            )
        else:
            data_set = test_data_set

        if data_set.get("number") == 1:
            result["cause"] = "First build of the container image"
            return result

        for _class in data_set["actions"]:
            if JENKINS_CLASS not in _class:
                continue
            # this class refers to cause of build / causeAction
            # which contains all the possible values for cause of build
            if _class[JENKINS_CLASS] == "hudson.model.CauseAction":
                for cause in _class["causes"]:
                    # refers to scm change
                    if cause[JENKINS_CLASS] == \
                            "hudson.triggers.SCMTrigger$SCMTriggerCause":
                        result["cause"] = cause[JENKINS_SHORT_DESCRIPTION]
                        break
                    # refers to parent child relationship / depends-on
                    elif cause[JENKINS_CLASS] == \
                            "hudson.model.Cause$UpstreamCause":
                        # process upstream project name
                        # eg: cccp/cccp-test-anomaly-latest
                        ups_proj = cause["upstreamProject"].split(
                            "/")[-1].split("-")
                        # form appid/jobid:desiredtag
                        ups_proj = "/".join(
                            ups_proj[1:-1]) + ":" + ups_proj[-1]
                        result["cause"] = "Parent container image {} is " \
                                          "rebuilt".format(ups_proj)
                        break
                    else:
                        result["cause"] = "Update to build configurations of " \
                                          "the container image"
                # fail over / if _class is not the one expected
                if not result.get("cause"):
                    # there are two _class available
                    # io.fabric8.jenkins.openshiftsync.BuildCause
                    # hudson.triggers.SCMTrigger$SCMTriggerCause
                    result["cause"] = \
                        _class["causes"][0][JENKINS_SHORT_DESCRIPTION]
        return result

    def get_stage_count(
            self, ordered_job_list, build_number, test_data_set=None
    ):
        """
        Gets the number of stages in a build of a project.
        :param ordered_job_list: The ordered list of jobs, with parents,
        followed by children
        :type ordered_job_list list
        :param build_number: The id of the build.
        :type build_number str
        :param test_data_set: data set to be used for test run.
        :type test_data_set dict
        :raises Exception
        :return: The number of stages in the project. None is returned on
        failure
        """
        result = None
        stages = None
        if not self.test:
            data_set = self.get_data_from_response(
                self.jenkins_workflow_client.describe_build_run(
                    ordered_job_list, build_number=build_number
                ),
                bad_json=True
            )
        else:
            data_set = test_data_set
        if data_set:
            stages = data_set.get("stages")
        if data_set and stages:
            result = len(stages)

        return result

    def get_stage_id(
            self, ordered_job_list, build_number, stage, stage_is_name=True,
            test_data_set=None
    ):
        """
        Gets the stage id, of a particular stage in a particular build of a
        project
        :param ordered_job_list: The ordered list of jobs, with parents,
        followed by children
        :type ordered_job_list list
        :param build_number: The id of the build.
        :type build_number str
        :param stage: The name of the pipeline stage of the build
        :type stage str
        :param stage_is_name: Default True, if true, stage is treated as name
        of stage, else it is treaded as stage number
        :type stage_is_name bool
        :param test_data_set: data set to be used for test run.
        :type test_data_set dict
        :raises Exception
        :return: The id of the stage, in build build_id in project
        ordered_job_list. None is returned on failure
        """
        result = None
        stages = None
        if not self.test:
            data_set = self.get_data_from_response(
                self.jenkins_workflow_client.describe_build_run(
                    ordered_job_list, build_number=build_number
                ),
                bad_json=True
            )
        else:
            data_set = test_data_set
        if data_set:
            stages = data_set.get("stages")
        if data_set and stages:
            if stage_is_name:
                for item in stages:
                    if item.get("name") == stage:
                        result = item.get("id")
                        break
            else:
                result = stages[int(stage)-1].get("id")

        return result

    def get_stage_name(
            self, ordered_job_list, build_number, stage_id, id_is_number=False,
            test_data_set=None
    ):
        """
        Gets the stage name, of a particular stage in a particular build of a
        project
        :param ordered_job_list: The ordered list of jobs, with parents,
        followed by children
        :type ordered_job_list list
        :param build_number: The id of the build.
        :type build_number str
        :param stage_id: The id/number of the pipeline stage of the build
        :type stage_id str
        :param id_is_number: Default is false, if True, stage id is treated as
        stage number
        :type id_is_number bool
        :param test_data_set: data set to be used for test run.
        :type test_data_set dict
        :raises Exception
        :return: The id of the stage, in build build_id in project
        ordered_job_list. None is returned on failure
        """
        result = None
        stages = None
        if not self.test:
            data_set = self.get_data_from_response(
                self.jenkins_workflow_client.describe_build_run(
                    ordered_job_list, build_number=build_number
                ),
                bad_json=True
            )
        else:
            data_set = test_data_set
        if data_set:
            stages = data_set.get("stages")
        if data_set and stages:
            if not id_is_number:
                for item in stages:
                    if item.get("id") == stage_id:
                        result = item.get("name")
                        break
            else:
                result = stages[int(stage_id)-1].get("name")

        return result

    def get_stage_flow_node_ids(
            self, ordered_job_list, build_number, node_number,
            test_data_set=None
    ):
        """
        Gets the stage flow node id the node where where a stage ran for build
        in project.
        :param ordered_job_list: The ordered list of jobs, with parents,
        followed by children
        :param build_number: The id of the build.
        :param node_number: The number of the node, this is usually the stage
        id got from get_stage_id
        :param test_data_set: data set to be used for test run.
        :return: The ids of the stage flow nodes, None on failure
        """
        result = None
        stage_flow_nodes = None
        stage_flow_node_ids = []
        if not self.test:
            data_set = self.get_data_from_response(
                self.jenkins_workflow_client.describe_execution_node(
                    ordered_job_list, build_number, node_number
                ),
                bad_json=True
            )
        else:
            data_set = test_data_set
        if data_set:
            stage_flow_nodes = data_set.get("stageFlowNodes")
        if data_set and stage_flow_nodes:
            for item in stage_flow_nodes:
                stage_flow_node_ids.append(
                    item.get("id")
                )
            result = stage_flow_node_ids
        return result

    def get_build_logs(
            self, ordered_job_list, build_number
    ):
        """
        Gets all the logs of a paticular build
        :param ordered_job_list: The ordered list of jobs, with parents,
        followed by children
        :type ordered_job_list list
        :param build_number: The id of the build
        :type build_number str
        :return: A list of dicts where each dict contains stage name, and stage
        logs, as returned by get_stage_logs
        stageflownodes.
        None is returned on failure
        """
        # TODO : Make this testable
        result = None
        stage_count = self.get_stage_count(
            ordered_job_list=ordered_job_list, build_number=build_number
        )
        if stage_count:
            result = []
            for i in range(1, stage_count):
                result.append(
                    {
                        "name": self.get_stage_name(
                            ordered_job_list=ordered_job_list,
                            build_number=build_number, stage_id=str(i),
                            id_is_number=True
                        ),
                        "logs": self.get_stage_logs(
                            ordered_job_list=ordered_job_list,
                            build_number=build_number, stage=str(i),
                            stage_is_name=False
                        )
                    }
                )
        return result

    def get_stage_logs(
            self, ordered_job_list, build_number, stage, stage_is_name=True,
            test_data_set=None
    ):
        """
        Gets the logs of a particular stage of a particular build of a project.
        :param ordered_job_list: The ordered list of jobs, with parents,
        followed by children
        :type ordered_job_list list
        :param build_number: The id of the build
        :type build_number str
        :param stage: The name of the stage whole logs are to be fetched
        :type stage str
        :param stage_is_name : Default True, if true, stage is treated as name
        of stage, else it is treaded as stage number
        :type stage_is_name bool
        :param test_data_set: data set to be used for test run.
        :return: A list of dicts where each dict contains name, desc and log of
        stageflownode.
        None is returned on failure
        """
        result = None
        stage_flow_nodes = None
        if not self.test:
            stage_id = self.get_stage_id(
                ordered_job_list, build_number=build_number, stage=stage,
                stage_is_name=stage_is_name
            )
        else:
            stage_id = self.get_stage_id(
                ordered_job_list, build_number=build_number, stage=stage,
                test_data_set=test_data_set[0]
            )
        if stage_id:
            if not self.test:
                stage_flow_nodes = self.get_stage_flow_node_ids(
                    ordered_job_list, build_number=build_number,
                    node_number=stage_id
                )
            else:
                stage_flow_nodes = self.get_stage_flow_node_ids(
                    ordered_job_list, build_number=build_number,
                    node_number=stage_id, test_data_set=test_data_set[1]
                )
        if stage_flow_nodes:
            if not self.test:
                result = []
                for n in stage_flow_nodes:
                    r = self.get_data_from_response(
                        self.jenkins_workflow_client.get_logs_of_execution_node(
                            ordered_job_list, build_number=build_number,
                            node_number=n
                        )
                    )
                    if r:
                        result.append(
                            {
                                "log": r.get("text"),
                                "name": r.get("name"),
                                "description": r.get("parameterDescription")
                            }
                        )
            else:
                result = [
                    stage_id,
                    stage_flow_nodes,
                    test_data_set[2].get("text")
                ]

        return result
