# Raspberry Pi Based Sensor Monitor for RuuviTag Sensors

![alt text](https://github.com/dhocker/sensor-monitor/raw/master/images/LCD-Example "LCD Example")

## Overview
This project is a Raspberry Pi (RPi) based sensor monitor for RuuviTag sensors. It is all
written in Python 3.

## Hardware Requirements

* a [Raspberry Pi](https://en.wikipedia.org/wiki/Raspberry_Pi#Networking) model 3 or 4 (one with WiFi and Bluetooth support)
* 2 4x20 [LCD panel](https://smile.amazon.com/dp/B086VVT4NH/). 
Any 4x20 LCD panel based on the PCF8574 controller for I2C should work.

# Installation and Setup

## RPi to LCD Connections

The following table summarizes the connections between the RPi
and the typical 4x20 LCD panel. Your LCD panel may come with jumper wires 
for interconnecting the RPi and LCD thus simplifying setup.

| RPi Pin | GPIO | RPi Name | Description      | LCD Pin               |
|---------|------|----------|------------------|-----------------------|
| 3       | 2    | SDA      | I2C data signal  | SDA         |
| 4       | -    | +5V      | Power to LCD     | Vcc         |
| 5       | 3    | SCL      | I2C clock signal | SCL         |
| 6       | -    | Ground   | Ground           | Gnd         |

## Install RPi Prerequisites

Be sure to check out the 
[ruuvitag-sensor instructions](https://github.com/ttu/ruuvitag-sensor/blob/master/install_guide_pi.md) 
for installing on an RPi. There is a significant number of prerequisite parts to be installed
before you can receive data from a RuuviTag.

At a minimum you need to install the following.

```shell
sudo apt-get install bluetooth bluez blueman
```
Reboot the RPi after installing the bluetooth packages.

## Enable I2C
Open raspi-config in a terminal session.
```shell
sudo raspi-config
```

Select "Interface Options" and then select "I2C". Choose "Yes" to enable I2C.

## Download Files
The easiest way to get the project files is to clone the GitHub repository.

```shell
git clone https://github.com/dhocker/sensor-monitor.git
```

## Create a VENV
Here, [virtualenv](https://virtualenv.pypa.io/en/latest/) and 
[virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/) are assumed.

```shell
mkvirtualenv -p python3 -r requirements.txt sensor-monitor3
```
## Create a Configuration File
sensor-monitor can be controlled through sensor_monitor.conf. Note that this file **is not**
part of the GitHub repo. The configuration file must be kept in the root directory of the project.

The configuration file is composed of JSON and looks like this.

```json
{
    "ruuvitags": {
        "XX:XX:XX:XX:XX:XX": {
            "name": "Kitchen"
        },
        "XX:XX:XX:XX:XX:XX": {
            "name": "OutDoor"
        }
    },
    "debug_sensors": "false",
    "log_level": "debug",
    "log_console": "true",
    "update_interval": 3.0,
    "offline_time": 600,
    "temperature_format": "F"
}
```

The most important use of the configuration file is to assign a human-readable name to a sensor.
Otherwise, your sensors will be shown with names derived from the last 4 digits of their mac.

| Key          | Description                                                            |
|--------------|------------------------------------------------------------------------|
| ruuvitags    | Defines a human-readable name for a given tag's mac                    |
| debug_sensors | When true, dumps each sensor's data into a file.                       |
| log_level    | debug, info, warning or error. Controls the verbosity of the log file. |
| log_console | When true, logs to file and to the console. |
| update_interval | Time between LCD updates expressed in seconds (as a float). |
| offline_time | If no data is received from a sensor in this time (seconds), the sensor is considered offline. |
| temperature_format | "F" for fahrenheit or "C" for centigrade. |

### How to Find a RuuviTag's mac
There are two ways to find a tag's mac (it is not on the sensor).

The first way is to use the Ruuvi app on an iPad, iPhone or Android phone. Activate one sensor at a time
and check the app to see what mac shows up.

The second way is to turn on "debug_sensors" in the configuration file and look at the 
[ruuvi.json](#ruuvitag-data) file it produces. Again, activate one sensor at a time.

## Install as Daemon (Optional)
You can easily install the sensor-monitor as a daemon. The following shell scripts facilitate
this process. Before using any of these scripts you should review each one. 

You may need to edit the sensormoniotrD.sh script to adjust for your VENV. If you followed these instructions
you should not need to make any changes.

While reviewing sensormonitorD.sh note that the daemon is configured to run as root. Older versions 
of Raspberry Pi OS required root permission to use I2C. That is no longer the case, so you can
change the DAEMON_USER variable to DAEMON_USER=pi if you want to avoid the root user in favor of the 
pi user.

| Script            | Use                                                                           |
|-------------------|-------------------------------------------------------------------------------|
| sensormoniotrD.sh | The daemon script that will be installed |
| installD.sh       | Installs sensor-moniotr as a daemon. sensor-monitor is automatically started. |
| uninstallD.sh     | Uninstalls sensor-monitor when previously installed as a daemon.              |
| startD.sh         | Starts the sensor-monitor daemon. |
| stopD.sh          | Stops the sensor-monitor if it is running. |
| restartD.sh       | Stops then starts the sensor-monitor daemon. |

You can always check the status of statusmonitorD.sh by running
```shell
service --status-all
```

## Run from Command Line
If you prefer to run sensor-monitor from a terminal, use the following commands.
```shell
workon sensor-monitor3
python sensor_monitor.py
```

# Reference

## RuuviTag Data
[Format 5 Reference](https://github.com/ruuvi/ruuvi-sensor-protocols/blob/master/dataformat_05.md)

Example of data returned by the ruuvitag-sensor module.
```json
{
    "D5:95:F0:51:21:F2": {
        "data_format": 5,
        "humidity": 49.55,
        "temperature": 25.66,
        "pressure": 1010.37,
        "acceleration": 1006.8326573964514,
        "acceleration_x": -172,
        "acceleration_y": -8,
        "acceleration_z": 992,
        "tx_power": 4,
        "battery": 3002,
        "movement_counter": 54,
        "measurement_sequence_number": 34834,
        "mac": "d595f05121f2"
    },
    "D5:68:78:B9:E0:F1": {
        "data_format": 5,
        "humidity": 49.95,
        "temperature": 25.2,
        "pressure": 1009.88,
        "acceleration": 1020.5802271257268,
        "acceleration_x": 20,
        "acceleration_y": 28,
        "acceleration_z": 1020,
        "tx_power": 4,
        "battery": 3146,
        "movement_counter": 26,
        "measurement_sequence_number": 58144,
        "mac": "d56878b9e0f1"
    }
}
```
