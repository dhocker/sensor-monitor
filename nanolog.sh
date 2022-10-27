#!/bin/bash

# nano /home/pi/rpi/sensor_monitor/sensor_monitor.log

echo 
echo Available log files
echo 

# Show list of available logs
x=-1
for i in *.log*; do
  x=$(($x + 1))
  echo $x - $i
  logs[$x]=$i
done

# Ask for log to be viewed
while true;
do
    echo
    read -p "Select log file to open (0-${x}): " sel
    if [[ $sel -ge 0 ]] &&  [[ $sel -le $x ]];
    then
        echo Selection: ${logs[$sel]}
        nano ${logs[$sel]}
        break
    else
        echo "Invalid selection"
    fi
done
