#!/usr/bin/python

import sys
sys.path.append('/storage/.kodi/addons/virtual.rpi-tools/lib')
import RPi.GPIO as GPIO
import os

# Pin is the pin number, using BCM numbering
gpio_button_number=3
gpio_led_number=18
GPIO.setmode(GPIO.BCM)

GPIO.setwarnings(False)

GPIO.setup(gpio_led_number, GPIO.OUT)
GPIO.output(gpio_led_number, GPIO.LOW)
GPIO.setup(gpio_button_number, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    GPIO.wait_for_edge(gpio_button_number, GPIO.FALLING)
    GPIO.output(gpio_led_number, GPIO.HIGH)
    # Insert whatever commands are necessary here
    
    GPIO.output(gpio_led_number, GPIO.LOW)
except:
    pass
GPIO.cleanup()
