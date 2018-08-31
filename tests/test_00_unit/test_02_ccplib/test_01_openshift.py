#!/usr/bin/env python2
# -*- coding: utf_8 -*-

import unittest

from ccp.lib.openshift import BuildInfo


class TestBuildInfo(unittest.TestCase):
    """
    Test the BuildInfo class responsible for
    extracting the build details
    """

    def setUp(self):
        self.buildinfo_obj = BuildInfo()
        self.sample_response = {
            "_class": "org.jenkinsci.plugins.workflow.job.WorkflowRun",
            "actions": [
                {
                    "_class": "hudson.model.CauseAction",
                    "causes": [
                        {
                            "_class": "io.fabric8.jenkins.openshiftsync.BuildCause",
                            "shortDescription": "OpenShift Build cccp/navidshaikh-anomaly-latest-2 from https://github.com/navidshaikh/anomaly"
                        },
                        {
                            "_class": "hudson.triggers.SCMTrigger$SCMTriggerCause",
                            "shortDescription": "Started by an SCM change"
                        }
                    ]
                },
                {
                    "_class": "hudson.model.ParametersAction",
                    "parameters": [
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "GIT_URL",
                            "value": "https://github.com/navidshaikh/anomaly"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "GIT_BRANCH",
                            "value": "master"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "GIT_PATH",
                            "value": "/"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "TARGET_FILE",
                            "value": "Dockerfile"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "DESIRED_TAG",
                            "value": "latest"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "NOTIFY_EMAIL",
                            "value": "shaikhnavid14@gmail.com"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "DEPENDS_ON",
                            "value": "None"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "BUILD_CONTEXT",
                            "value": "./"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "PIPELINE_NAME",
                            "value": "navidshaikh-anomaly-latest"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "APP_ID",
                            "value": "navidshaikh"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "JOB_ID",
                            "value": "anomaly"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "PRE_BUILD_SCRIPT",
                            "value": "None"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "PRE_BUILD_CONTEXT",
                            "value": "None"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "REGISTRY_URL",
                            "value": "172.29.33.48:5000"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "PIPELINE_REPO_DIR",
                            "value": "/tmp/pipeline-service"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "APP_ID",
                            "value": "navidshaikh"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "JOB_ID",
                            "value": "anomaly"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "GIT_PATH",
                            "value": "/"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "PRE_BUILD_SCRIPT",
                            "value": "None"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "PRE_BUILD_CONTEXT",
                            "value": "None"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "DEPENDS_ON",
                            "value": "None"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "DESIRED_TAG",
                            "value": "latest"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "PIPELINE_NAME",
                            "value": "navidshaikh-anomaly-latest"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "BUILD_CONTEXT",
                            "value": "./"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "REGISTRY_URL",
                            "value": "172.29.33.48:5000"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "PIPELINE_REPO_DIR",
                            "value": "/tmp/pipeline-service"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "GIT_BRANCH",
                            "value": "master"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "GIT_URL",
                            "value": "https://github.com/navidshaikh/anomaly"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "TARGET_FILE",
                            "value": "Dockerfile"
                        },
                        {
                            "_class": "hudson.model.StringParameterValue",
                            "name": "NOTIFY_EMAIL",
                            "value": "shaikhnavid14@gmail.com"
                        }
                    ]
                },
                {
                    "_class": "hudson.plugins.git.util.BuildData",
                    "buildsByBranchName": {
                        "origin/master": {
                            "_class": "hudson.plugins.git.util.Build",
                            "buildNumber": 2,
                            "buildResult": None,
                            "marked": {
                                "SHA1": "7e8996417ad7aa438d13190122e895b96914f952",
                                "branch": [
                                    {
                                        "SHA1": "7e8996417ad7aa438d13190122e895b96914f952",
                                        "name": "origin/master"
                                    }
                                ]
                            },
                            "revision": {
                                "SHA1": "7e8996417ad7aa438d13190122e895b96914f952",
                                "branch": [
                                    {
                                        "SHA1": "7e8996417ad7aa438d13190122e895b96914f952",
                                        "name": "origin/master"
                                    }
                                ]
                            }
                        }
                    },
                    "lastBuiltRevision": {
                        "SHA1": "7e8996417ad7aa438d13190122e895b96914f952",
                        "branch": [
                            {
                                "SHA1": "7e8996417ad7aa438d13190122e895b96914f952",
                                "name": "origin/master"
                            }
                        ]
                    },
                    "remoteUrls": [
                        "https://github.com/navidshaikh/anomaly"
                    ],
                    "scmName": ""
                },
                {
                    "_class": "hudson.plugins.git.GitTagAction"
                },
                {
                    "_class": "hudson.plugins.git.util.BuildData",
                    "buildsByBranchName": {
                        "refs/remotes/origin/email-1": {
                            "_class": "hudson.plugins.git.util.Build",
                            "buildNumber": 2,
                            "buildResult": None,
                            "marked": {
                                "SHA1": "ed0abc5efdc359a90808f5a07f743dd05c3e6f96",
                                "branch": [
                                    {
                                        "SHA1": "ed0abc5efdc359a90808f5a07f743dd05c3e6f96",
                                        "name": "refs/remotes/origin/email-1"
                                    }
                                ]
                            },
                            "revision": {
                                "SHA1": "ed0abc5efdc359a90808f5a07f743dd05c3e6f96",
                                "branch": [
                                    {
                                        "SHA1": "ed0abc5efdc359a90808f5a07f743dd05c3e6f96",
                                        "name": "refs/remotes/origin/email-1"
                                    }
                                ]
                            }
                        }
                    },
                    "lastBuiltRevision": {
                        "SHA1": "ed0abc5efdc359a90808f5a07f743dd05c3e6f96",
                        "branch": [
                            {
                                "SHA1": "ed0abc5efdc359a90808f5a07f743dd05c3e6f96",
                                "name": "refs/remotes/origin/email-1"
                            }
                        ]
                    },
                    "remoteUrls": [
                        "https://github.com/navidshaikh/ccp-openshift"
                    ],
                    "scmName": ""
                },
                {
                    "_class": "org.jenkinsci.plugins.workflow.cps.EnvActionImpl"
                },
                {
                    "_class": "org.jenkinsci.plugins.workflow.job.views.FlowGraphAction"
                }
            ],
            "artifacts": [
            ],
            "building": False,
            "description": "OpenShift Build cccp/navidshaikh-anomaly-latest-2 from https://github.com/navidshaikh/anomaly",
            "displayName": "#2",
            "duration": 85872,
            "estimatedDuration": 85447,
            "executor": None,
            "fullDisplayName": "cccp » cccp/navidshaikh-anomaly-latest #2",
            "id": "2",
            "keepLog": False,
            "number": 2,
            "queueId": 189,
            "result": "SUCCESS",
            "timestamp": 1534501562890,
            "url": "https://jenkins-cccp.172.29.33.23.nip.io/job/cccp/job/cccp-navidshaikh-anomaly-latest/2/",
            "changeSets": [
            ],
            "nextBuild": None,
            "previousBuild": {
                "number": 1,
                "url": "https://jenkins-cccp.172.29.33.23.nip.io/job/cccp/job/cccp-navidshaikh-anomaly-latest/1/"
            }
        }

    def test_parse_cause_of_build_1(self):
        """
        ccp.lib.openshift: Test parsing cause of build case-1 (Git commit)
        from REST API JSON response containing Jenkins job details
        """
        self.assertEqual(
            self.buildinfo_obj.parse_cause_of_build(
                self.sample_response),
            """\
Git commit 7e8996417ad7aa438d13190122e895b96914f952 to branch \
origin/master of repo https://github.com/navidshaikh/anomaly."""
        )

    def test_parse_cause_of_build_2(self):
        """
        cccp.lib.openshift: Test parsing cause of build case-2 (parent proj)
        from REST API JSON response containing Jenkins job details
        case-2: Upstream project is rebuilt
        """
        # trimmed unneeded lines from sample response
        sample_response = {
            "number": 2,
            "_class": "org.jenkinsci.plugins.workflow.job.WorkflowRun",
            "actions": [
                {
                    "_class": "hudson.model.CauseAction",
                    "causes": [
                        {
                            "_class": "io.fabric8.jenkins.openshiftsync.BuildCause",
                            "shortDescription": "OpenShift Build cccp/test-python-release-2 from https://github.com/bamachrn/cccp-python"
                        },
                        {
                            "_class": "hudson.model.Cause$UpstreamCause",
                            "shortDescription": "Started by upstream project \"cccp/cccp-test-anomaly-latest\" build number 1",
                            "upstreamBuild": 1,
                            "upstreamProject": "cccp/cccp-test-anomaly-latest",
                            "upstreamUrl": "job/cccp/job/cccp-test-anomaly-latest/"
                        }
                    ]
                }
            ]
        }
        self.assertEqual(
            self.buildinfo_obj.parse_cause_of_build(
                sample_response),
            "Upstream/parent container test/anomaly:latest is rebuilt"
        )

    def test_parse_cause_of_build_3(self):
        """
        cccp.lib.openshift: Test parsing cause of build case-3 (first build)
        from REST API JSON response containing Jenkins job details
        case-3: First build of container
        """
        # trimmed unneeded lines from sample response
        sample_response = {"number": 1}
        self.assertEqual(
            self.buildinfo_obj.parse_cause_of_build(
                sample_response),
            "First build of the container"
        )

    def test_parse_cause_of_build_4(self):
        """
        cccp.lib.openshift: Test parsing cause of build case-4 (config update)
        from REST API JSON response containing Jenkins job details
        case-4: Update to build configurations of the container
        """
        # trimmed unneeded lines from sample response
        sample_response = {
            "number": 5,
            "_class": "org.jenkinsci.plugins.workflow.job.WorkflowRun",
            "actions": [
                {
                    "_class": "hudson.model.CauseAction",
                    "causes": [
                        {
                            "_class": "io.fabric8.jenkins.openshiftsync.BuildCause",
                            "shortDescription": "OpenShift Build cccp/test-python-release-5 from https://github.com/bamachrn/cccp-python"
                        }
                    ]
                }
            ]
        }
        self.assertEqual(
            self.buildinfo_obj.parse_cause_of_build(
                sample_response),
            "Update to build configurations of the container"
        )

    def test_parse_cause_of_build_5(self):
        """
        cccp.lib.openshift: Test parsing cause of build case-5 (failure)
        from REST API JSON response containing Jenkins job details
        case-5: Unable to find the cause build.
        """
        self.assertRaises(
            self.buildinfo_obj.parse_cause_of_build({}))

        self.assertEqual(
            self.buildinfo_obj.parse_cause_of_build({}),
            "Unable to find the cause of build.")

    def test_parse_jenkins_job(self):
        """
        ccp.lib.openshift: Test parsing build info from
        REST API JSON response containing Jenkins job details
        """
        expected_response = {
            'PIPELINE_REPO_DIR': '/tmp/pipeline-service',
            'PRE_BUILD_CONTEXT': 'None',
            'JOB_ID': 'anomaly',
            'NOTIFY_EMAIL': 'shaikhnavid14@gmail.com',
            'TARGET_FILE': 'Dockerfile',
            'PRE_BUILD_SCRIPT': 'None',
            'DEPENDS_ON': 'None',
            'GIT_URL': 'https://github.com/navidshaikh/anomaly',
            'APP_ID': 'navidshaikh',
            'BUILD_CONTEXT': './',
            'GIT_PATH': '/',
            'DESIRED_TAG': 'latest',
            'GIT_BRANCH': 'master',
            'CAUSE_OF_BUILD': """Git commit \
7e8996417ad7aa438d13190122e895b96914f952 to branch origin/master \
of repo https://github.com/navidshaikh/anomaly.""",
            'REGISTRY_URL': '172.29.33.48:5000',
            'PIPELINE_NAME': 'navidshaikh-anomaly-latest',
            'RESULT': 'SUCCESS'}

        self.assertEqual(
            self.buildinfo_obj.parse_jenkins_job(
                self.sample_response),
            expected_response
        )


if __name__ == "__main__":
    unittest.main()
