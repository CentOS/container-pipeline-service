import os
import urllib

DUFFY_SSID = os.environ.get('DUFFY_SSID')
URL_BASE = os.environ.get('URL_BASE')
API = os.environ.get('API')

print (DUFFY_SSID, URL_BASE, API)

done_nodes_url = "%s/Node/done?key=%s&ssid=%s" % (URL_BASE, API, DUFFY_SSID)
resp = urllib.urlopen(done_nodes_url).read()
