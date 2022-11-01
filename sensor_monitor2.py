#
# sensor_monitor.py - RuuviTag sensor data monitor
# Copyright © 2022 Dave Hocker
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# See the LICENSE file for more details.
#


import os
import sys
import datetime
import signal
import logging
from time import sleep
from json import dumps, dump
import app_logger
from sensor_thread import SensorThread
from configuration import Configuration
from i2c_lcd_driver import LCD


class SensorMonitor():
    def __init__(self, the_sensor_thread, the_lcd, page_interval=3.0, offline_time=600, temperature_format="F",
                 debug_sensors=False, sensor_config={}, logger=None):
        self._the_sensor_thread = the_sensor_thread
        self._the_lcd = the_lcd
        self._page_interval = page_interval
        self._offline_time = offline_time
        self._temperature_format = temperature_format
        self._debug_sensors = debug_sensors
        self._sensor_config = sensor_config
        self. _known_sensors = []
        self._logger = logger
        self._terminate_monitor = False

    def terminate(self):
        self._terminate_monitor = True

    @staticmethod
    def to_fahrenheit(centigrade):
        """
        Convert centigrade to fahrenheit
        """
        return 32.0 + (centigrade * 1.8)

    def _mac_name(self, mac):
        """
        Return the human-readable name for a RuuviTag mac
        """
        # Try the configuration file first
        if mac in self._sensor_config.keys():
            return self._sensor_config[mac]["name"]

        # Fall back to the last 4 digits of the mac
        return mac[(len(mac) - 5):].replace(":", "")

    @staticmethod
    def _now_str(now_dt):
        """
        Return a formatted string containing the current date and time
        :return:
        """
        # custom format to remove unwanted leading zeros
        ampm = "am"
        if now_dt.hour >= 12:
            ampm = "pm"
        hour = now_dt.hour
        if hour > 12:
            hour -= 12
        return f"{now_dt.year:4d}-{now_dt.month:02d}-{now_dt.day:02d}  {hour:2d}:{now_dt.minute:02d} {ampm}"
        # return now_dt.strftime("%Y-%m-%d %I:%M %p")

    def _update_sensor_display(self, current_data):
        """
        Update the LCD with current sensor data. A 4x20 LCD is assumed.
        :param current_data: A dict of sensor data keyed by sensor mac
        :return:
        """
        # Update LCD
        number_sensors = len(current_data.keys())
        line = 0
        col = 0
        for mac in current_data.keys():
            # Reference for sensor data: https://github.com/ruuvi/ruuvi-sensor-protocols/blob/master/dataformat_05.md
            # Update display for this sensor
            data_age = datetime.datetime.now() - current_data[mac]["timestamp"]
            # If the data is older than "offline_time" seconds consider the sensor offline
            if data_age.seconds < self._offline_time:
                tmp = current_data[mac]['temperature']
                if self._temperature_format == "F":
                    tmp = SensorMonitor.to_fahrenheit(tmp)
                hum = current_data[mac]['humidity']
            else:
                # We have not received sensor data within the offline_time value
                tmp = 0.0
                hum = 0.0
                logger = logging.getLogger("sensor_monitor")
                logger.warning(f"Sensor {self._mac_name(mac)} {mac} appears to be offline")
            self._the_lcd.lcd_display_string(f"{self._mac_name(mac):7s} {tmp:5.1f} {hum:5.1f}", line + 1, col)

            # Roll the line counter
            if line == 2 and number_sensors > 3:
                # Wait before moving on to the next page of sensor data
                sleep(self._page_interval)
                line = 0
                self._the_lcd.lcd_clear_line(2)
                self._the_lcd.lcd_clear_line(3)
                number_sensors -= 3
            else:
                line += 1

    def run(self):
        first_pass = True
        while not self._terminate_monitor:
            try:
                current_data = self._the_sensor_thread.sensor_list

                if self._debug_sensors:
                    # Diagnostic data dump
                    fp = open("ruuvitag.json", "w")
                    dump(current_data, fp, indent=4)
                    fp.close()

                # Keep track of known sensors
                for mac in current_data.keys():
                    if mac not in self._known_sensors:
                        self._logger.info(f"Monitoring sensor {mac} {self._mac_name(mac)}")
                        self._known_sensors.append(mac)

                for mac in self._known_sensors:
                    if mac not in current_data.keys():
                        self._logger.info(f"Sensor {mac} {self._mac_name(mac)} has gone offline")
                        self._known_sensors.remove(mac)

                # Update date and time at the start of every minute
                now_dt = datetime.datetime.now()
                if now_dt.second < 10 or first_pass:
                    dtstr = SensorMonitor._now_str(now_dt)
                    self._the_lcd.lcd_display_string(dtstr, 4, 0)

                # Update sensor display. Note that this may take
                # several update_intervals
                self._update_sensor_display(current_data)

                # Wait for the next interval
                first_pass = False
                sleep(self._page_interval)

            except KeyboardInterrupt:
                self._logger.info("ctrl-c caught in SensorMonitor.run()")
                self._terminate_monitor = True
            except Exception as ex:
                self._terminate_monitor = True
                self._logger.error("Unhandled exception is sensor_monitor.main()")
                self._logger.error(str(ex))
                self._logger.error("sensor_monitor terminating")


def main():
    """
    Monitor main
    :return:
    """

    terminate_monitor = False
    logger_name = "sensor_monitor"
    the_sensor_monitor = None

    # Clean up when killed
    def term_handler(signum, frame):
        # logger.info("AtHomePowerlineServer received kill signal...shutting down")
        # This will break the forever loop at the foot of main()
        the_sensor_monitor.terminate()
        logger.info("sensor_monitor terminate signal handled")
        clean_up()
        sys.exit(0)

    # Orderly clean up of the server
    def clean_up():
        # Clean up resources allocated at monitor start
        thd.close()
        the_lcd.lcd_clear()
        logger.info("sensor_monitor shutdown complete")
        logger.info("################################################################################")
        app_logger.shut_down()

    # Change the current directory so we can find the configuration file.
    just_the_path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(just_the_path)

    # Load configuration
    Configuration.load_configuration()
    config = Configuration.get_configuration()
    update_interval = config[Configuration.CFG_UPDATE_INTERVAL]
    offline_time = config[Configuration.CFG_OFFLINE_TIME]
    temperature_format = config[Configuration.CFG_TEMPERATURE_FORMAT].upper()
    tf = config[Configuration.CFG_DEBUG_SENSORS].lower()
    debug_sensors = (tf == "true") or (tf == "yes")
    sensor_config = config[Configuration.CFG_RUUVITAGS]

    # Start logging
    app_logger.start(logger_name)
    logger = logging.getLogger(logger_name)
    logger.info("sensor_monitor starting...")

    # Start the sensor monitor
    thd = SensorThread()
    thd.open()

    # Open the LCD
    the_lcd = LCD()

    # Create a singleton sensor monitor
    the_sensor_monitor = SensorMonitor(thd, the_lcd, page_interval=update_interval, offline_time=offline_time,
                                       temperature_format=temperature_format, debug_sensors=debug_sensors,
                                       sensor_config=sensor_config, logger=logger
                                      )

    # Set up handler for the kill signal
    signal.signal(signal.SIGTERM, term_handler)

    try:
        the_sensor_monitor.run()
    except KeyboardInterrupt:
        logger.info("ctrl-c caught in main()")
        terminate_monitor = True
    except Exception as ex:
        terminate_monitor = True
        logger.error("Unhandled exception is sensor_monitor.main()")
        logger.error(str(ex))
        logger.error("sensor_monitor terminating")

    # Terminate the sensor thread and clear the LCD
    clean_up()


if __name__ == "__main__":
    main()