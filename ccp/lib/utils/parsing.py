import ast
import base64
import json
import yaml
from ccp.lib.utils.print_out import print_out


def encode(data):
    """
    Applies base64 encoding to passed string
    :param data: The string to encode
    :type data: str
    :return: Encoded string
    """
    return base64.b64encode(data)


def decode(data):
    """
    Decodes a base64 encoded string.
    :param data: The encoded string to decode
    :type data: str
    :return: The decoded string
    """
    return base64.b64decode(data)


def json_to_python(data):
    """
    Parses the json and loads the data
    :param data: The json data to parse as string
    :type data: str
    :raises Exception
    :return: Pythonic representation of json data
    """
    return json.loads(data)


def parse_literals(data):
    """
    Parses literal, use to parse of string contains
    quotes.
    :param data The data to be parsed as literal as a string.
    :type data: str
    :raises Exception
    :return: Pythonic representation of data
    """
    return ast.literal_eval(data)


def read_yaml(filepath, verbose=True):
    """
    Read the YAML file at specified location
    raise an exception upon failure reading/load the file
    :param filepath: The path of the yaml file to load
    :type filepath str
    :param verbose: Default True: If true, error is printed
    :type verbose: bool
    :return the yaml data on success
    """
    try:
        with open(filepath) as fin:
            data = yaml.load(fin, Loader=yaml.BaseLoader)
    except yaml.YAMLError as exc:
        if verbose:
            print_out("Failed to read {}".format(filepath))
            print_out("Error: {}".format(exc))
        return None
    else:
        return data
