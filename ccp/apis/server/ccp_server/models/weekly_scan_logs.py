# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from ccp_server.models.base_model_ import Model
from ccp_server.models.all_scanner_logs import AllScannerLogs  # noqa: F401,E501
from ccp_server.models.meta import Meta  # noqa: F401,E501
from ccp_server import util


class WeeklyScanLogs(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, meta: Meta=None, build: str=None, status: str=None, logs: AllScannerLogs=None):  # noqa: E501
        """WeeklyScanLogs - a model defined in Swagger

        :param meta: The meta of this WeeklyScanLogs.  # noqa: E501
        :type meta: Meta
        :param build: The build of this WeeklyScanLogs.  # noqa: E501
        :type build: str
        :param status: The status of this WeeklyScanLogs.  # noqa: E501
        :type status: str
        :param logs: The logs of this WeeklyScanLogs.  # noqa: E501
        :type logs: AllScannerLogs
        """
        self.swagger_types = {
            'meta': Meta,
            'build': str,
            'status': str,
            'logs': AllScannerLogs
        }

        self.attribute_map = {
            'meta': 'meta',
            'build': 'build',
            'status': 'status',
            'logs': 'logs'
        }

        self._meta = meta
        self._build = build
        self._status = status
        self._logs = logs

    @classmethod
    def from_dict(cls, dikt) -> 'WeeklyScanLogs':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The WeeklyScanLogs of this WeeklyScanLogs.  # noqa: E501
        :rtype: WeeklyScanLogs
        """
        return util.deserialize_model(dikt, cls)

    @property
    def meta(self) -> Meta:
        """Gets the meta of this WeeklyScanLogs.


        :return: The meta of this WeeklyScanLogs.
        :rtype: Meta
        """
        return self._meta

    @meta.setter
    def meta(self, meta: Meta):
        """Sets the meta of this WeeklyScanLogs.


        :param meta: The meta of this WeeklyScanLogs.
        :type meta: Meta
        """

        self._meta = meta

    @property
    def build(self) -> str:
        """Gets the build of this WeeklyScanLogs.


        :return: The build of this WeeklyScanLogs.
        :rtype: str
        """
        return self._build

    @build.setter
    def build(self, build: str):
        """Sets the build of this WeeklyScanLogs.


        :param build: The build of this WeeklyScanLogs.
        :type build: str
        """

        self._build = build

    @property
    def status(self) -> str:
        """Gets the status of this WeeklyScanLogs.


        :return: The status of this WeeklyScanLogs.
        :rtype: str
        """
        return self._status

    @status.setter
    def status(self, status: str):
        """Sets the status of this WeeklyScanLogs.


        :param status: The status of this WeeklyScanLogs.
        :type status: str
        """

        self._status = status

    @property
    def logs(self) -> AllScannerLogs:
        """Gets the logs of this WeeklyScanLogs.


        :return: The logs of this WeeklyScanLogs.
        :rtype: AllScannerLogs
        """
        return self._logs

    @logs.setter
    def logs(self, logs: AllScannerLogs):
        """Sets the logs of this WeeklyScanLogs.


        :param logs: The logs of this WeeklyScanLogs.
        :type logs: AllScannerLogs
        """

        self._logs = logs