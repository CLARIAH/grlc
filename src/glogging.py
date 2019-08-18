import logging

import grlc.static as static

def getGrlcLogger(name):
    glogger = logging.getLogger(name)
    if static.LOG_DEBUG_MODE:
        glogger.setLevel(logging.DEBUG)
    return glogger
