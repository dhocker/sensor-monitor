#
# configuraton.py - sensor monitor configuration
# © 2022 by Dave Hocker
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# See the LICENSE file for more details.
#
# Currently, it looks like this:
#
# {
#     "ruuvitags": {
#         {"mac1": "tag_name1"},
#         {"mac2": "tag_name2"},
#         {"mac3": "tag_name3"}
#     }
# }
#
# The JSON parser is quite finicky about strings being quoted as shown above.
#
# This class behaves like a singleton class. There is only one instance of the configuration.
# There is no need to create an instance of this class, as everything about it is static.
#


import json


class Configuration():
    # Essentially a singleton instance of the configuration
    _active_config = None

    # Keys
    CFG_RUUVITAGS = "ruuvitags"
    CFG_DEBUG_SENSORS = "debug_sensors"
    CFG_LOG_LEVEL = "log_level"
    CFG_LOG_CONSOLE = "log_console"
    CFG_UPDATE_INTERVAL = "update_interval"
    CFG_OFFLINE_TIME = "offline_time"  # in seconds
    CFG_TEMPERATURE_FORMAT = "temperature_format"  # F or C
    CFG_BACKLIGHT_OFF_AT = "backlight_off_at"
    CFG_BACKLIGHT_ON_AT = "backlight_on_at"

    def __init__(self):
        Configuration.load_configuration()

    # Load the configuration file
    @classmethod
    def load_configuration(cls):
        # Try to open the conf file. If there isn't one, we give up.
        cfg_path = None
        try:
            cfg_path = Configuration.get_configuration_file()
            # print("Opening configuration file {0}".format(cfg_path))
            cfg = open(cfg_path, 'r')
        except Exception as ex:
            print("Unable to open {0}".format(cfg_path))
            print(str(ex))
            return

        # Read the entire contents of the conf file
        cfg_json = cfg.read()
        cfg.close()
        # print cfg_json

        # Try to parse the conf file into a Python structure
        try:
            cls._active_config = json.loads(cfg_json)
        except Exception as ex:
            print("Unable to parse configuration file as JSON")
            print(str(ex))
            return

        # print str(Configuration.ActiveConfig)
        return

    @classmethod
    def dump_configuration(cls):
        """
        Print the configuration
        :return: None
        """
        print("Active configuration file")
        print(json.dumps(cls._active_config))

    @classmethod
    def get_configuration(cls):
        """
        Return the current configuration
        :return: The configuration as a dict
        """
        return cls._active_config

    @classmethod
    def get_configuration_file(cls):
        """
        Returns the full path to the configuration file
        """
        file_name = "sensor_monitor.conf"
        return file_name
