# Thumby main.py- quick initialization and splashscreen before menu.py is called
# Last updated 17-Jan-2023

from machine import freq, mem32, reset
freq(133_000_000)

if(mem32[0x4005800C]==1): # WDT scratch register '0'
    from time import sleep_ms
    mem32[0x4005800C]=0
    gamePath=''
    conf = open("thumby.cfg", "r").read().split(',')
    for k in range(len(conf)):
        if(conf[k] == "lastgame"):
            gamePath = conf[k+1]
    try:
        freq(125_000_000)
        __import__(gamePath)
    except ImportError:
        print("Couldn't load "+gamePath)
        sleep_ms(500)
    except:
        print("Script error... :(")
        sleep_ms(500)
    finally:
        reset()


from machine import Pin, SPI
from st7735 import ST7735

HWID = 1
IDPin = Pin(15, Pin.IN, Pin.PULL_DOWN)

i2c = None
spi = SPI(0, polarity=0, phase=0, sck=Pin(18), mosi=Pin(19))
display = ST7735(96, 56, spi, dc=Pin(17), res=Pin(20), cs=Pin(16))
display.init_display()

open('lib/TClogo.bin', 'rb').readinto(display.buffer)
display.show()


import menu


reset()