import ast
import base64
import json


def encode(data):
    """
    Applyies base64 encoding to passed string
    :param data: The string to encode
    :type data str
    :return: Encoded string.
    """
    return base64.b64encode(data)


def decode(data):
    """
    Decodes a base64 encoded string.
    :param data: The encoded string to decode
    :return: The decoded string
    """
    return base64.b64decode(data)


def json_to_python(data):
    """
    Parses the json and loads the data
    :param data: The json data to parse as string
    :type data str
    :raises Exception
    :return: Pythonic repersentation of json data
    """
    p = None
    try:
        p = json.loads(data)
    except Exception as ex:
        raise ex
    return p


def parse_literals(data):
    """
    Parses literal, use to parse of string contains
    quotes.
    :param data The data to be parsed as literal as a string.
    :type data str
    :raises Exception
    :return: Pythonic repersentation of data
    """
    p = None
    try:
        p = ast.literal_eval(data)
    except Exception as ex:
        raise ex
    return p
