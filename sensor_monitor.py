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


def debug_sensors():
    """
    Returns True if the debug_sensor configuration property is True
    """
    config = Configuration.get_configuration()
    tf = config[Configuration.CFG_DEBUG_SENSORS].lower()
    return tf == "true" or tf == "yes"


def to_fahrenheit(centigrade):
    """
    Convert centigrade to fahrenheit
    """
    return 32.0 + (centigrade * 1.8)


def mac_name(mac):
    """
    Return the human-readable name for a RuuviTag mac
    """
    # Try the configuration file first
    config = Configuration.get_configuration()
    sensor_db = config[Configuration.CFG_RUUVITAGS]
    if mac in sensor_db.keys():
        return sensor_db[mac]["name"]

    # Fall back to the last 4 digits of the mac
    return mac[(len(mac) - 5):].replace(":", "")


def now_str(now_dt):
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
    return f"{now_dt.year}-{now_dt.month}-{now_dt.day}  {hour:2d}:{now_dt.minute:02d} {ampm}"
    # return now_dt.strftime("%Y-%m-%d %I:%M %p")


def update_sensor_display(the_lcd, current_data, page_interval, offline_time=600, temperature_format="F"):
    """
    Update the LCD with current sensor data. A 4x20 LCD is assumed.
    :param the_lcd: The LCD to be updated
    :param current_data: A dict of sensor data keyed by sensor mac
    :param page_interval: Paging wait interval
    :param offline_time: Age of data when sensor is considered offline
    :param temperature_format: Fahrenheit or Centigrade, F or C
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
        if data_age.seconds < offline_time:
            tmp = current_data[mac]['temperature']
            if temperature_format == "F":
                tmp = to_fahrenheit(tmp)
            hum = current_data[mac]['humidity']
        else:
            # We have not received sensor data within the offline_time value
            tmp = 0.0
            hum = 0.0
            logger = logging.getLogger("sensor_monitor")
            logger.warning(f"Sensor {mac_name(mac)} {mac} appears to be offline")
        the_lcd.lcd_display_string(f"{mac_name(mac):7s} {tmp:5.1f} {hum:5.1f}", line + 1, col)

        # Roll the line counter
        if line == 2 and number_sensors > 3:
            # Wait before moving on to the next page of sensor data
            sleep(page_interval)
            line = 0
            the_lcd.lcd_clear_line(2)
            the_lcd.lcd_clear_line(3)
            number_sensors -= 3
        else:
            line += 1


def main():
    """
    Monitor main
    :return:
    """

    terminate_monitor = False
    logger_name = "sensor_monitor"

    # Clean up when killed
    def term_handler(signum, frame):
        # logger.info("AtHomePowerlineServer received kill signal...shutting down")
        # This will break the forever loop at the foot of main()
        terminate_monitor = True
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

    # Start logging
    app_logger.start(logger_name)
    logger = logging.getLogger(logger_name)
    logger.info("sensor_monitor starting...")

    # Start the sensor monitor
    thd = SensorThread()
    thd.open()

    # Open the LCD
    the_lcd = LCD()

    # Set up handler for the kill signal
    signal.signal(signal.SIGTERM, term_handler)

    known_sensors = []
    first_pass = True
    while not terminate_monitor:
        try:
            current_data = thd.sensor_list

            if debug_sensors():
                # Diagnostic data dump
                fp = open("ruuvitag.json", "w")
                dump(current_data, fp, indent=4)
                fp.close()

            # Keep track of known sensors
            for mac in current_data.keys():
                if mac not in known_sensors:
                    logger.info(f"Monitoring sensor {mac} {mac_name(mac)}")
                    known_sensors.append(mac)

            for mac in known_sensors:
                if mac not in current_data.keys():
                    logger.info(f"Sensor {mac} {mac_name(mac)} has gone offline")
                    known_sensors.remove(mac)

            # Update date and time at the start of every minute
            now_dt = datetime.datetime.now()
            if now_dt.second < 10 or first_pass:
                dtstr = now_str(now_dt)
                the_lcd.lcd_display_string(dtstr, 4, 0)

            # Update sensor display. Note that this may take
            # several update_intervals
            update_sensor_display(the_lcd, current_data, update_interval,
                                  offline_time=offline_time, temperature_format=temperature_format)

            # Wait for the next interval
            first_pass = False
            sleep(update_interval)

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
    # print("Sensor-Monitor ended")
