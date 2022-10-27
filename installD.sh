#!/bin/bash

### Install AtHomePowerlineServerD.sh as a daemon

# Installation steps
sudo cp sensormonitorD.sh /etc/init.d/sensormonitorD.sh
sudo chmod +x /etc/init.d/sensormonitorD.sh
sudo update-rc.d sensormonitorD.sh defaults

# Start the daemon: 
sudo service sensormonitorD.sh start

exit 0

