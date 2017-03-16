import os
import urllib

from ci.lib import _print

DUFFY_SSID = os.environ.get('DUFFY_SSID')
URL_BASE = os.environ.get('URL_BASE')
API = os.environ.get('API')
DEBUG = os.environ.get('CI_DEBUG', None) == 'true'
BUILD_FAILED = os.environ.get('BUILD_FAILED', None) == 'true'

print (DUFFY_SSID, URL_BASE)


def fail_nodes():
    fail_nodes_url = "{url_base}/Node/fail?key={key}&ssid={ssid}".format(
        url_base=URL_BASE, key=API, ssid=DUFFY_SSID)
    resp = urllib.urlopen(fail_nodes_url).read()
    _print(resp)


def clean_nodes():
    done_nodes_url = "%s/Node/done?key=%s&ssid=%s" % (
        URL_BASE, API, DUFFY_SSID)
    resp = urllib.urlopen(done_nodes_url).read()
    _print(resp)


if __name__ == '__main__':
    if DEBUG and BUILD_FAILED:
        fail_nodes()
    else:
        clean_nodes()
