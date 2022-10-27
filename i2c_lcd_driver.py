# -*- coding: utf-8 -*-

# The code that served as the base for this work was found at
# https://www.circuitbasics.com/raspberry-pi-i2c-lcd-set-up-and-programming/
# Reworked by Dave Hocker in September 2022
# The reworked code is subject to the GPL v3 license.
# The starting code was obtained from the above link.

# From https://www.circuitbasics.com/raspberry-pi-i2c-lcd-set-up-and-programming/
# This attribution was in that code.
# Original code found at:
# https://gist.github.com/DenisFromHR/cc863375a6e19dce359d

"""
Compiled, mashed and generally mutilated 2014-2015 by Denis Pleic
Made available under GNU GENERAL PUBLIC LICENSE

# Modified Python I2C library for Raspberry Pi
# as found on http://www.recantha.co.uk/blog/?p=4849
# Joined existing 'i2c_lib.py' and 'lcddriver.py' into a single library
# added bits and pieces from various sources
# By DenisFromHR (Denis Pleic)
# 2015-02-10, ver 0.1

"""

# Replaced smbus with smbus2
import smbus2 as smbus
from time import sleep


class I2CDevice:
    # Find this by running ls -al /dev/i2c*
    # i2c bus (0 -- original Pi, 1 -- Rev 2 Pi)
    # I2CBUS = 0
    # For RPi model 3B and RPi 4B. Uses GPIO 2 and 3.
    I2CBUS = 1

    def __init__(self, addr, port=I2CBUS):
        self._addr = addr
        self._bus = smbus.SMBus(port)

    # Write a single command
    def write_cmd(self, cmd):
        self._bus.write_byte(self._addr, cmd)
        sleep(0.0001)

    # Write a command and argument
    def write_cmd_arg(self, cmd, data):
        self._bus.write_byte_data(self._addr, cmd, data)
        sleep(0.0001)

    # Write a block of data
    def write_block_data(self, cmd, data):
        self._bus.write_block_data(self._addr, cmd, data)
        sleep(0.0001)

    # Read a single byte
    def read(self):
        return self._bus.read_byte(self._addr)

    # Read
    def read_data(self, cmd):
        return self._bus.read_byte_data(self._addr, cmd)

    # Read a block of data
    def read_block_data(self, cmd):
        return self._bus.read_block_data(self._addr, cmd)

    def close(self):
        """
        Clean up, free resources
        :return:
        """
        self._bus.close()
        del self._bus
        self._bus = None


class LCD:
    """
    A PCF8574 based LCD panel class
    """
    # commands
    LCD_CLEARDISPLAY = 0x01
    LCD_RETURNHOME = 0x02
    LCD_ENTRYMODESET = 0x04
    LCD_DISPLAYCONTROL = 0x08
    LCD_CURSORSHIFT = 0x10
    LCD_FUNCTIONSET = 0x20
    LCD_SETCGRAMADDR = 0x40
    LCD_SETDDRAMADDR = 0x80

    # flags for display entry mode
    LCD_ENTRYRIGHT = 0x00
    LCD_ENTRYLEFT = 0x02
    LCD_ENTRYSHIFTINCREMENT = 0x01
    LCD_ENTRYSHIFTDECREMENT = 0x00

    # flags for display on/off control
    LCD_DISPLAYON = 0x04
    LCD_DISPLAYOFF = 0x00
    LCD_CURSORON = 0x02
    LCD_CURSOROFF = 0x00
    LCD_BLINKON = 0x01
    LCD_BLINKOFF = 0x00

    # flags for display/cursor shift
    LCD_DISPLAYMOVE = 0x08
    LCD_CURSORMOVE = 0x00
    LCD_MOVERIGHT = 0x04
    LCD_MOVELEFT = 0x00

    # flags for function set
    LCD_8BITMODE = 0x10
    LCD_4BITMODE = 0x00
    LCD_2LINE = 0x08
    LCD_1LINE = 0x00
    LCD_5x10DOTS = 0x04
    LCD_5x8DOTS = 0x00

    # flags for backlight control
    LCD_BACKLIGHT = 0x08
    LCD_NOBACKLIGHT = 0x00

    En = 0b00000100  # Enable bit
    Rw = 0b00000010  # Read/Write bit
    Rs = 0b00000001  # Register select bit

    def __init__(self, device=None, address=0x27, rows=4, cols=20):
        """
        Initializes objects and lcd
        For PCF8574 based LCD (run i2cdetect -y 1)
        :param device: An I2CDevice instance to use with the LCD panel
        :param address: The I2C address of the LCD panel
        """
        if device is None:
            self._lcd_device = I2CDevice(address)
        else:
            self._lcd_device = device
        self._rows = rows
        self._cols = cols

        self._lcd_write(0x03)
        self._lcd_write(0x03)
        self._lcd_write(0x03)
        self._lcd_write(0x02)

        self._lcd_write(LCD.LCD_FUNCTIONSET | LCD.LCD_2LINE | LCD.LCD_5x8DOTS | LCD.LCD_4BITMODE)
        self._lcd_write(LCD.LCD_DISPLAYCONTROL | LCD.LCD_DISPLAYON)
        self._lcd_write(LCD.LCD_CLEARDISPLAY)
        self._lcd_write(LCD.LCD_ENTRYMODESET | LCD.LCD_ENTRYLEFT)
        sleep(0.2)

    # clocks EN to latch command
    def _lcd_strobe(self, data):
        self._lcd_device.write_cmd(data | LCD.En | LCD.LCD_BACKLIGHT)
        sleep(.0005)
        self._lcd_device.write_cmd(((data & ~LCD.En) | LCD.LCD_BACKLIGHT))
        sleep(.0001)

    def _lcd_write_four_bits(self, data):
        self._lcd_device.write_cmd(data | LCD.LCD_BACKLIGHT)
        self._lcd_strobe(data)

    # write a command to lcd
    def _lcd_write(self, cmd, mode=0):
        self._lcd_write_four_bits(mode | (cmd & 0xF0))
        self._lcd_write_four_bits(mode | ((cmd << 4) & 0xF0))

    # write a character to lcd (or character rom) 0x09: backlight | RS=DR<
    # works!
    def lcd_write_char(self, charvalue, mode=1):
        self._lcd_write_four_bits(mode | (charvalue & 0xF0))
        self._lcd_write_four_bits(mode | ((charvalue << 4) & 0xF0))

    def lcd_display_string(self, string, line=1, pos=0):
        """
        put string function with optional char positioning
        :param string: Character string to be written to line, pos
        :param line: Line number 1-n
        :param pos: Character position on line, 0-(line_length-1)
        :return: None
        """
        # An empty string is a line clear
        if len(string) == 0:
            string = [" " for i in range(self._cols)]
        if line == 1:
            pos_new = pos
        elif line == 2:
            pos_new = 0x40 + pos
        elif line == 3:
            pos_new = 0x14 + pos
        elif line == 4:
            pos_new = 0x54 + pos
        else:
            # Undefined
            pos_new = 0

        self._lcd_write(0x80 + pos_new)

        for char in string:
            self._lcd_write(ord(char), LCD.Rs)

    def lcd_clear_line(self, line):
        """
        Clear a line
        :param line:
        :return:
        """
        self.lcd_display_string("", line, 0
                                )
    # clear lcd and set to home
    def lcd_clear(self):
        self._lcd_write(LCD.LCD_CLEARDISPLAY)
        self._lcd_write(LCD.LCD_RETURNHOME)

    # define backlight on/off (lcd.backlight(1); off= lcd.backlight(0)
    def backlight(self, state):  # for state, 1 = on, 0 = off
        if state == 1:
            self._lcd_device.write_cmd(LCD.LCD_BACKLIGHT)
        elif state == 0:
            self._lcd_device.write_cmd(LCD.LCD_NOBACKLIGHT)

    # add custom characters (0 - 7)
    # See https://www.circuitbasics.com/raspberry-pi-i2c-lcd-set-up-and-programming/
    def lcd_load_custom_chars(self, fontdata):
        self._lcd_write(0x40);
        for char in fontdata:
            for line in char:
                self.lcd_write_char(line)

    def lcd_close(self):
        """
        Clean up resources
        :return: None
        """
        self._lcd_device.close()
        del self._lcd_device
        self._lcd_device = None
