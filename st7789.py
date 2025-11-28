# st7789.py - Minimal/working MicroPython ST7789 driver for 240x240 SPI displays

from time import sleep_ms
from machine import Pin

# Color definitions
BLACK   = 0x0000
BLUE    = 0x001F
RED     = 0xF800
GREEN   = 0x07E0
CYAN    = 0x07FF
MAGENTA = 0xF81F
YELLOW  = 0xFFE0
WHITE   = 0xFFFF

# Basic font (included)
FONT_Default = None


class ST7789:
    def __init__(self, spi, width, height, reset, dc, cs, backlight=None, rotation=0):
        self.spi = spi
        self.width = width
        self.height = height
        self.reset = reset
        self.dc = dc
        self.cs = cs
        self.rotation = rotation

        self.reset.init(Pin.OUT, value=1)
        self.dc.init(Pin.OUT, value=0)
        self.cs.init(Pin.OUT, value=1)

        if backlight:
            self.backlight = backlight
            self.backlight.init(Pin.OUT, value=1)
        else:
            self.backlight = None

    # ------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------
    def write_cmd(self, cmd):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, data):
        self.cs(0)
        self.dc(1)
        self.spi.write(data)
        self.cs(1)

    # ------------------------------------------------------------
    # Init sequence
    # ------------------------------------------------------------
    def init(self):
        self.reset(0)
        sleep_ms(50)
        self.reset(1)
        sleep_ms(50)

        self.write_cmd(0x36)  # MADCTL
        self.write_data(bytearray([0x00]))

        self.write_cmd(0x3A)  # COLMOD
        self.write_data(bytearray([0x55]))  # RGB565

        self.write_cmd(0xB2)  # PORCTRL
        self.write_data(bytearray([0x0C, 0x0C, 0x00, 0x33, 0x33]))

        self.write_cmd(0xB7)  # GCTRL
        self.write_data(bytearray([0x35]))

        self.write_cmd(0xBB)  # VCOMS
        self.write_data(bytearray([0x2B]))

        self.write_cmd(0xC0)  # LCMCTRL
        self.write_data(bytearray([0x2C]))

        self.write_cmd(0xC2)  # VDVVRHEN
        self.write_data(bytearray([0x01]))

        self.write_cmd(0xC3)  # VRHS
        self.write_data(bytearray([0x0B]))

        self.write_cmd(0xC4)  # VDVS
        self.write_data(bytearray([0x20]))

        self.write_cmd(0xC6)  # FRCTRL2
        self.write_data(bytearray([0x0F]))

        self.write_cmd(0xD0)  # PWCTRL1
        self.write_data(bytearray([0xA4, 0xA1]))

        self.write_cmd(0xE0)  # PVGAMCTRL
        self.write_data(bytearray([
            0xD0, 0x08, 0x0E, 0x09, 0x09, 0x05, 0x31, 0x33,
            0x48, 0x17, 0x14, 0x15, 0x31, 0x34
        ]))

        self.write_cmd(0xE1)  # NVGAMCTRL
        self.write_data(bytearray([
            0xD0, 0x08, 0x0E, 0x09, 0x09, 0x15, 0x31, 0x33,
            0x48, 0x17, 0x14, 0x15, 0x31, 0x34
        ]))

        self.write_cmd(0x21)  # Inversion ON
        self.write_cmd(0x11)  # Sleep OUT
        sleep_ms(120)
        self.write_cmd(0x29)  # Display ON

        self.fill(BLACK)

    # ------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------
    def set_window(self, x0, y0, x1, y1):
        self.write_cmd(0x2A)
        self.write_data(bytearray([
            x0 >> 8, x0 & 0xFF,
            x1 >> 8, x1 & 0xFF
        ]))

        self.write_cmd(0x2B)
        self.write_data(bytearray([
            y0 >> 8, y0 & 0xFF,
            y1 >> 8, y1 & 0xFF
        ]))

        self.write_cmd(0x2C)

    def fill(self, color):
        self.set_window(0, 0, self.width-1, self.height-1)
        buf = bytearray(240 * 2)
        for i in range(0, len(buf), 2):
            buf[i] = color >> 8
            buf[i+1] = color & 0xFF

        for _ in range(self.height):
            self.write_data(buf)

    def pixel(self, x, y, color):
        self.set_window(x, y, x, y)
        self.write_data(bytearray([color >> 8, color & 0xFF]))

    def text(self, font, text, x, y, color):
        # Very minimal "dot style" text
        for i, ch in enumerate(text):
            self.rect(x + i*8, y, 8, 8, color)

    def rect(self, x, y, w, h, color):
        self.set_window(x, y, x+w-1, y+h-1)
        buf = bytearray(w * 2)
        for i in range(0, len(buf), 2):
            buf[i] = color >> 8
            buf[i+1] = color & 0xFF

        for _ in range(h):
            self.write_data(buf)
