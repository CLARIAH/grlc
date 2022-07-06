# /*
# * SPDX-License-Identifier: MIT
# * SPDX-FileCopyrightText: Copyright (c) 2022 Orange SA
# *
# * Author: Mihary RANAIVOSON
# * Modifications: Before, only DEBUG mode was taken account
# */


# # grlc_fork: local modules
# import static as static

# grlc_fork: remote modules
import grlc_fork.static as static

# other imports
import logging


def getGrlcLogger(name):
    """Construct a logger for grlc with the logging level specified on `config.ini`."""
    
    glogger = logging.getLogger(name)
    log_level = static.LOG_LEVEL.lower()
    
    if log_level in [ "critical", "50" ]:
        glogger.setLevel(logging.CRITICAL)
        logging.basicConfig(level=logging.CRITICAL)
    
    elif log_level in [ "error", "40" ]:
        glogger.setLevel(logging.ERROR)
        logging.basicConfig(level=logging.ERROR)
    
    elif log_level in [ "warning", "30" ]:
        glogger.setLevel(logging.WARNING)
        logging.basicConfig(level=logging.WARNING)
        
    elif log_level in [ "info", "20" ]:
        glogger.setLevel(logging.INFO)
        logging.basicConfig(level=logging.INFO)

    elif log_level in [ "debug", "10" ]:
        glogger.setLevel(logging.DEBUG)
        logging.basicConfig(level=logging.DEBUG)

    elif log_level in [ "notset", "0" ]:
        glogger.setLevel(logging.NOTSET)
        logging.basicConfig(level=logging.NOTSET)

    else:
        glogger.setLevel(logging.INFO)
        logging.basicConfig(level=logging.INFO)

    return glogger