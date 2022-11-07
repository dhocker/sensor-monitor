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
import rtc_sync
from sensor_thread import SensorThread
from configuration import Configuration
from backlight import BacklightState
from i2c_lcd_driver import LCD


class SensorMonitor():
    def __init__(self,
                 the_sensor_thread,
                 the_lcd,
                 page_interval=3.0,
                 offline_time=600,
                 temperature_format="F",
                 debug_sensors=False,
                 sensor_config={},
                 backlight_off_time="23:00",
                 backlight_on_time="06:00",
                 logger=None):
        """
        Construct an instance of the sensor monitor
        :param the_sensor_thread: An instance of the SensorThread class (the data source)
        :param the_lcd: An instance of the LCD class (the LCD panel)
        :param page_interval: The amount of time to display a page (in seconds)
        :param offline_time: A sensor is considered offline if no data is received in this time (seconds)
        :param temperature_format: F or C (fahrenheit or centigrade)
        :param debug_sensors: Dump sensor data to ruuvi.json
        :param sensor_config: A dict keyed by mac. From the current configuration file.
        :param backlight_off_time: HH:MM when backlight goes off
        :param backlight_on_time: HH:MM when backlight comes of
        :param logger: An instance of the logger to be used for all output.
        """
        self._the_sensor_thread = the_sensor_thread
        self._the_lcd = the_lcd
        self._page_interval = page_interval
        self._offline_time = offline_time
        self._temperature_format = temperature_format
        self._debug_sensors = debug_sensors
        self._sensor_config = sensor_config
        self. _known_sensors = []
        self._logger = logger
        self._backlight_state = BacklightState(off_at=backlight_off_time, on_at=backlight_on_time)
        self._terminate_monitor = False

        # Dimensions of expected LCD panel
        self._rows = 4
        self._cols = 20

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

    def _update_time_display(self):
        """
        Displays the current date and time on the bottom row of the display
        :return:
        """
        now_dt = datetime.datetime.now()
        dtstr = SensorMonitor._now_str(now_dt)
        self._the_lcd.lcd_display_string(dtstr, self._rows, 0)

    def _update_sensor_display(self, current_data):
        """
        Update the LCD with current sensor data. A 4x20 LCD is assumed.
        :param current_data: A dict of sensor data keyed by sensor mac
        :return:
        """
        # Generate all the lines to be displayed
        display_lines = []
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
                self._logger.warning(f"Sensor {self._mac_name(mac)} {mac} appears to be offline")

            display_lines.append(f"{self._mac_name(mac):7s} {tmp:5.1f} {hum:5.1f}")

        # Alpha sort of lines
        display_lines.sort()

        number_sensors_to_display = len(display_lines)
        line_num = 0

        # Display lines with paging
        self._the_lcd.lcd_clear()
        self._update_time_display()
        for a_line in display_lines:
            self._the_lcd.lcd_display_string(a_line, line_num + 1, 0)

            # Roll the line counter
            if line_num == 2 and number_sensors_to_display > 3:
                # Wait before moving on to the next page of sensor data
                sleep(self._page_interval)
                line_num = 0
                self._the_lcd.lcd_clear()
                self._update_time_display()
                number_sensors_to_display -= 3
            else:
                line_num += 1

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

                # Update sensor display. Note that this may take
                # several update_intervals
                if self._backlight_state.query_backlight_state():
                    self._the_lcd.backlight(1)
                    self._update_sensor_display(current_data)
                else:
                    self._the_lcd.backlight(0)

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


class MainProgram():
    """
    The main program encapsulated in a class
    """
    def __init__(self):
        self._logger_name = "sensor_monitor"
        self._the_sensor_monitor = None
        self._thd = None
        self._the_lcd = None
        self._cleanup_complete = False
        self._logger = None
    
    def run(self):
        """
        Monitor main
        :return:
        """
        
        
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
        backlight_off_at = config[Configuration.CFG_BACKLIGHT_OFF_AT]
        backlight_on_at = config[Configuration.CFG_BACKLIGHT_ON_AT]
        
        # Start logging
        app_logger.start(self._logger_name)
        self._logger = logging.getLogger(self._logger_name)
        self._logger.info("sensor_monitor starting...")
        
        # Sync the system clock
        try:
            rtc_sync.sync_system_clock()
        except ValueError as ex:
            self._logger.error("An exception occurred while attempting to sync the system clock")
            self._logger.error(str(ex))
        
        # Start the sensor monitor
        self._thd = SensorThread()
        self._thd.open()
        
        # Open the LCD
        self._the_lcd = LCD()
        
        # Create a singleton sensor monitor based on the config file
        self._the_sensor_monitor = SensorMonitor(self._thd, self._the_lcd,
                                                 page_interval=update_interval,
                                                 offline_time=offline_time,
                                                 temperature_format=temperature_format,
                                                 debug_sensors=debug_sensors,
                                                 sensor_config=sensor_config,
                                                 logger=self._logger,
                                                 backlight_off_time=backlight_off_at,
                                                 backlight_on_time=backlight_on_at
                                                 )
        
        # Set up handler for the terminate signal 15
        signal.signal(signal.SIGTERM, self._terminate_handler)
        
        try:
            self._the_sensor_monitor.run()
        except KeyboardInterrupt:
            self._logger.info("ctrl-c caught in MainProgram.run()")
        except Exception as ex:
            self._logger.error("Unhandled exception is sensor_monitor.run()")
            self._logger.error(str(ex))
            self._logger.error("sensor_monitor terminating")
        
        # Terminate the sensor thread and clear the LCD
        if not self._cleanup_complete:
            self._clean_up()

    # Clean up when killed
    def _terminate_handler(self, signum, frame):
        # self._logger.info("AtHomePowerlineServer received kill signal...shutting down")
        self._logger.info(f"sensor_monitor terminate signal {signum} handled")
        self._clean_up()
        sys.exit(0)

    # Orderly clean up of the server
    def _clean_up(self):
        # This will break the forever loop
        self._the_sensor_monitor.terminate()
        # Clean up resources allocated at monitor start
        self._thd.close()
        self._the_lcd.backlight(1)
        self._the_lcd.lcd_clear()
        self._the_lcd.lcd_close()

        self._logger.info("sensor_monitor shutdown complete")
        self._logger.info("################################################################################")
        app_logger.shut_down()
        self._cleanup_complete = True


if __name__ == "__main__":
    main = MainProgram()
    main.run()
