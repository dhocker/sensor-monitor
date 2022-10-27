#!/bin/bash

### Uninstall (remove) sensormonitorD.sh as a daemon

# Uninstall steps
sudo service sensormonitorD.sh stop
sudo rm /etc/init.d/sensormonitorD.sh
sudo update-rc.d -f sensormonitorD.sh remove

exit 0

