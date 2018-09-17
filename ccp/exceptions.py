"""
This script defines custom exceptions of the service.
"""


class InvalidPipelineName(Exception):
    """
    Exception to be raised when pipeline name populated doesn't
    confornt to allowed value for openshift template field metadata.name
    """
    pass


class ErrorAccessingIndexEntryAttributes(Exception):
    """
    Exception to be raised when there are errors accessing
    index entry attributes
    """
    pass
