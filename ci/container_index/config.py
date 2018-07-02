"""
This file contains the configurations needed for index ci
"""

# The list of default schema validations that need to run.
schema_validators = [
    "IDValidator",
    "AppIDValidator",
    "JobIDValidator",
    "DesiredTagValidator",
    "UniqueEntryValidator",
    "GitURLValidator",
    "GitPathValidator",
    "GitBranchValidator",
    "TargetFileValidator",
    "NotifyEmailValidator",
    "BuildContextValidator"
]

# The list of default value validators that need to run.
value_validators = [
    "GitCloneValidator",
    "CccpYamlExistsValidator"
]
