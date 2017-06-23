#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    # Hack to make packages in project root dir importable
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "container_pipeline.lib.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
