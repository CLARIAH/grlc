from pythonql.parser.Preprocessor import makeProgramFromString
from six import PY3

import grlc.glogging as glogging

glogger = glogging.getGrlcLogger(__name__)

def project(dataIn, projectionScript):
    '''Programs may make use of data in the `dataIn` variable and should
    produce data on the `dataOut` variable.'''
    # We don't really need to initialize it, but we do it to avoid linter errors
    dataOut = {}
    try:
        projectionScript = str(projectionScript)
        program = makeProgramFromString(projectionScript)
        if PY3:
            loc = {
                'dataIn': dataIn,
                'dataOut': dataOut
            }
            exec(program, {}, loc)
            dataOut = loc['dataOut']
        else:
            exec(program)
    except Exception as e:
        glogger.error("Error while executing SPARQL projection")
        glogger.error(projectionScript)
        glogger.error("Encountered exception: ")
        glogger.error(e)
        dataOut = {
            'status': 'error',
            'message': e.message
        }
    return dataOut
