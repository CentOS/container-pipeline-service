"""
This file contains base classes of query processor.
"""

from ccp.lib.utils.parsing import json_to_python, parse_literals


class QueryProcessor(object):
    """
    Acts as base of all Query Processor
    """
    pass


class JSONQueryProcessor(QueryProcessor):
    """
    Acts as base of JSONQueryProcessor
    """

    @staticmethod
    def get_data_from_response(response, bad_json=False):
        """
        Extracts data from a requests response object
        :param response: The response from which we need to extract information
        :type response requests.response
        :param bad_json: Default False: If true, uses ast eval instead of json
        load
        :type bad_json bool
        :return: response result in pythonic form, if it can get it, Else None
        :raises Exception
        """
        data = None
        if response:
            if not bad_json:
                try:
                    data = json_to_python(response.text)
                except Exception:
                    data = parse_literals(response.text)
            else:
                data = parse_literals(response.text)
        return data