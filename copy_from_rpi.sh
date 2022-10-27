# copy_from_rpi raspberrypi-xxx folder filename

if [ $# = 3 ]; then
  scp pi@$1:/home/pi/rpi/$2/$3 $3
else
  echo copy_from_rpi rpiname directory file
fi
