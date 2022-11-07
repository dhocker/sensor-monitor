#
# sensor_thread.py - RuuviTag sensor data collection
# Copyright © 2022 Dave Hocker
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# See the LICENSE file for more details.
#


from datetime import datetime


class BacklightState():
    def __init__(self, off_at, on_at):
        """
        Create a backlight state tracker. This is a simple table
        that indicates the desired backlight state for every minute of the day.
        :param off_at: HH:MM when backlight goes off
        :param on_at: HH:MM when backlight comes on
        """
        # State table for every minute of the day initialized to backlight on
        # Note that backlight state is the value 0 (off) or 1 (on)
        self._backlight_state_table = [1 for i in range(24 * 60)]

        # Initialize the state table
        on_dt = datetime.strptime(on_at, "%H:%M")
        on_minute = (on_dt.hour * 60) + on_dt.minute
        off_dt = datetime.strptime(off_at, "%H:%M")
        off_minute = (off_dt.hour * 60) + off_dt.minute

        # Start with the off time and go forward until the on time is reached
        while off_minute != on_minute:
            self._backlight_state_table[off_minute] = 0
            off_minute += 1
            if off_minute >= len(self._backlight_state_table):
                off_minute = 0

    def query_backlight_state(self):
        """
        Return the desired state of the backlight for the current time
        :return: 0 or 1
        """
        now = datetime.now()
        return self.query_backlight_state_dt(now)

    def query_backlight_state_dt(self, for_time_dt):
        """
        Return the desired state of the backlight for a given time
        :param for_time_dt: Return the backlight state for this time
        :return:
        """
        minute = (for_time_dt.hour * 60 ) + for_time_dt.minute

        # Return the state for the specified minute
        return self._backlight_state_table[minute]
