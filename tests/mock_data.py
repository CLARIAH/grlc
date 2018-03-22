from mock import Mock
from os import path
from glob import glob

base_url = 'tests/repo/'
def buildEntry(entryName):
    entryName = entryName.replace(base_url, '')
    return {
        u'download_url': entryName,
         u'name': entryName,
         u'path': entryName,
         u'type': u'file'
    }
mock_files = [ buildEntry(f) for f in glob(base_url + '*') ]

def mock_requestsGithub(uri, headers={}, params={}):
    if uri.endswith('contents'):
        return_value = Mock(ok=True)
        return_value.json.return_value = mock_files
        return return_value
    else:
        targetFile = uri.replace('https://raw.githubusercontent.com/fakeuser/fakerepo/master/', base_url)
        if path.exists(targetFile):
            f = open(targetFile, 'r')
            lines = f.readlines()
            text = ''.join(lines)
            return_value = Mock(status_code=200)
            return_value.text = text
            return return_value
        else:
            return_value = Mock(status_code=404)
            return return_value
