#!/usr/bin/env python3
"""
main.py
Created on: 2025-11-28
Author: Stefano Selmin <s.selmin@orion-srl.it>

Esempio base MicroPython per display ST7789 240x240 tramite SPI
"""

from machine import Pin, SPI
import time
import st7789

TFT_WIDTH = 240
TFT_HEIGHT = 240

PIN_CS  = 5
PIN_DC  = 16
PIN_RST = 17
PIN_BL  = 4

spi = SPI(
    1,
    baudrate=40000000,
    polarity=1,
    phase=1,
    sck=Pin(18),
    mosi=Pin(23),
    miso=None
)

display = st7789.ST7789(
    spi,
    TFT_WIDTH,
    TFT_HEIGHT,
    reset=Pin(PIN_RST),
    dc=Pin(PIN_DC),
    cs=Pin(PIN_CS),
    backlight=Pin(PIN_BL),
    rotation=0
)

def main():
    Pin(PIN_BL, Pin.OUT).value(1)

    display.init()
    display.fill(st7789.BLACK)

    display.text(st7789.FONT_Default, "Hello ST7789!", 20, 110, st7789.RED)

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
