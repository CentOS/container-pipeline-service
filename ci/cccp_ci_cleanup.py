import os

from ci.lib import _print, run_cmd

DUFFY_SSID = os.environ.get('DUFFY_SSID')
DEBUG = os.environ.get('CI_DEBUG', None) == 'true'
BUILD_FAILED = os.environ.get('BUILD_FAILED', None) == 'true'

print DUFFY_SSID


def clean_nodes():
    _print("Cleaning nodes")
    _print(run_cmd(
        'export CICO_API_KEY=`cat ~/duffy.key` && '
        'cico node done %s' % DUFFY_SSID))


if __name__ == '__main__':
    # if DEBUG and BUILD_FAILED:
    #     fail_nodes()
    # else:
    clean_nodes()
