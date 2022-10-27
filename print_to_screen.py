"""
Print sensor data to the screen.
Press Ctrl+C to quit.
Sensor:      F4:A5:74:89:16:57
TOD:         2017-02-02 13:45:25.233400
Temperature: 72 F
Humidity:    28 %
Pressure:    689 hPa
"""

# pylint: disable=duplicate-code

import os
from datetime import datetime
from threading import Thread
from time import sleep
from json import dumps, dump

from ruuvitag_sensor.ruuvi import RuuviTagSensor, RunFlag

# Change here your own device's mac-address
mac = ['D5:95:F0:51:21:F2']
data_point_count = 0

print('Starting')


def to_fahrenheit(centigrade):
    return 32.0 + (centigrade * 1.8)


def print_data(received_data):
    global data_point_count
    data_point_count += 1

    received_mac = received_data[0]
    data = received_data[1]
    tod = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    line_sen = str.format('Sensor:      {0}', received_mac)

    line_tod = f"Date/Time: {tod}"

    # line_tem = str.format('Temperature: {0} C', data['temperature'])
    line_tem = str.format('Temperature: {0:.2f} F', to_fahrenheit(data['temperature']))

    line_hum = str.format('Humidity:    {0:.2f} %', data['humidity'])

    line_pre = str.format('Pressure:    {0:.2f} hPa', data['pressure'])

    line_tod = f"TOD:         {str(datetime.now())}"
    line_count = f"Count:       {data_point_count}"

    # Clear screen and print sensor data
    os.system('clear')
    print('Press Ctrl+C to quit.\n\r\n\r')
    print(line_sen)
    print(line_tod)
    print(line_count)
    print(line_tem)
    print(line_hum)
    print(line_pre)
    print('\n\r\n\r.......')


class SensorThread(Thread):
    def __init__(self):
        self._data_point_count = 0
        self._runflag = RunFlag()
        super().__init__()

    def run(self):
        try:
            RuuviTagSensor.get_data(self.handle_sensor_data, mac, run_flag=self._runflag)
            print("RuuviTagSensor.get_data() ended")
        except Exception as ex:
            print("Unhandled exception caught in SensorThread.run()")
            print(str(ex))

    def handle_sensor_data(self, received_data):
        self._data_point_count += 1

        fp = open("sensor.json", "w")
        dump(received_data, fp, indent=4)
        fp.close()

        received_mac = received_data[0]
        data = received_data[1]

        line_sen = str.format('Sensor:      {0}', received_mac)

        # line_tem = str.format('Temperature: {0} C', data['temperature'])
        line_tem = str.format('Temperature: {0:.2f} F', to_fahrenheit(data['temperature']))

        line_hum = str.format('Humidity:    {0:.2f} %', data['humidity'])

        line_pre = str.format('Pressure:    {0:.2f} hPa', data['pressure'])

        line_tod = f"TOD:         {str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}"
        line_count = f"Count:       {self._data_point_count}"

        # Clear screen and print sensor data
        os.system('clear')
        print('Press Ctrl+C to quit.\n\r\n\r')
        print(line_sen)
        print(line_tod)
        print(line_count)
        print(line_tem)
        print(line_hum)
        print(line_pre)
        print("\n\r")
        print(dumps(received_data, indent=4))
        print('\n\r\n\r.......')

    def terminate(self):
        self._runflag.running = False


if __name__ == "__main__":
    # RuuviTagSensor.get_data(print_data, mac)
    thd = SensorThread()
    thd.start()
    print("Waiting for SensorThread to end")

    run = True
    while run:
        try:
            sleep(1.0)
        except KeyboardInterrupt:
            run =  False
            thd.terminate()
            print("ctrl-c caught in main()")
            thd.join()

    print("SensorThread example ended")
