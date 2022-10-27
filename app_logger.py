#
# app_logger.py - application logging support
# © 2022 by Dave Hocker AtHomeX10@gmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# See the LICENSE file for more details.
#

import logging
import logging.handlers
import os
from configuration import Configuration


def start(logger_name):
    """
    Set up logging for the application using the sensor_monitor logger
    :return:
    """

    # Default overrides
    logformat = '%(asctime)s, %(threadName)s, %(module)s, %(levelname)s, %(message)s'
    logdateformat = '%Y-%m-%d %H:%M:%S'

    # Remove any existing configuration. However, this results in
    # output to the console. To avoid this, we send it to the null device.
    try:
        null_dev = open(os.devnull, 'w')
        logging.basicConfig(force=True, format=logformat, datefmt=logdateformat, stream=null_dev)
    except Exception as ex:
        # This isn't a terminal error, but we need to let it be known
        print("Unable to reset basic logging config")
        print(str(ex))

    # Logging level override
    config = Configuration.get_configuration()
    log_level_override = config[Configuration.CFG_LOG_LEVEL].lower()
    if log_level_override == "debug":
        loglevel = logging.DEBUG
    elif log_level_override == "info":
        loglevel = logging.INFO
    elif log_level_override == "warn":
        loglevel = logging.WARNING
    elif log_level_override == "error":
        loglevel = logging.ERROR
    else:
        loglevel = logging.DEBUG

    # Configure the sensor_monitor logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(loglevel)

    formatter = logging.Formatter(logformat, datefmt=logdateformat)

    # Do we log to console?
    if config[Configuration.CFG_LOG_CONSOLE].lower() == "true":
        ch = logging.StreamHandler()
        ch.setLevel(loglevel)
        ch.setFormatter(formatter)
        # logger.addHandler(ch)
        logger.addHandler(ch)

    # Always log to a file
    logfile = "sensor_monitor.log"
    fh = logging.handlers.TimedRotatingFileHandler(logfile, when='midnight', backupCount=3)
    fh.setLevel(loglevel)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.debug("Logging to file: %s", logfile)


# Controlled logging shutdown
def shut_down():
    logging.shutdown()
    print("Logging shutdown")
