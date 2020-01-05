#
# Communicate with an Arduino that wants to know the time
#

import serial
import time
import xbmcgui
import xbmcaddon
from datetime import datetime
from libs.utility import debugTrace, errorTrace, infoTrace, newPrint, now

action = sys.argv[1]

debugTrace("-- Entered clocksync.py with action " + action + " --")

# Action should be "loud" or "quiet" to turn dialogs on/off
if action == "loud":
    show_dialog = True
else:
    show_dialog = False


# Set the addon name for use in the dialogs
addon = xbmcaddon.Addon("service.zomboided.tools")
addon_name = addon.getAddonInfo("name")

def getYYMMDDwHHMMSS():
    # Datetime object containing current date and time
    now = datetime.now()
    dt_string = now.strftime("%y%m%d%w%H%M%S")
    return dt_string


def sendToArduino(send_buffer):
    # Write a message to the Arduino
    debugTrace("Sending " + send_buffer)
    ser.write(send_buffer)


def receiveFromArduino():
    # Listen for a message from the Arduino wrapped in start and end markers
    global startMarker, endMarker

    char_buffer = ""
    char = " "
    byte_count = 0
    started = False

    while ser.inWaiting() > 0:
        char = ser.read()
        
        if ord(char) == startMarker:
            started = True
        elif ord(char) == endMarker:
            # Return message
            debugTrace("Got message : " + char_buffer)
            return char_buffer
        else:
            if started:
                char_buffer = char_buffer + char
                byte_count += 1
                
    # Don't return messages that aren't surrounded by markers
    return ""


def getMessageFromArduino(message, timeout):
    # Wait until the Arduino sends a message, or we get fed up waiting
    debugTrace("Waiting for Arduino to send " + message)
    waited = 0
    msg = ""
    while msg.find(message) == -1:    
        while ser.inWaiting() == 0:
            time.sleep(1)
            waited += 1
            # Time out if we've waited long enough and not got a message
            if waited >= timeout:
                errorTrace("clocksync.py", "Timed out waiting for " + message + " from Arduino")
                return None                
        msg = receiveFromArduino()
    # Return message found
    return msg
        
        
# Set the baud rate, must be the same as the Arduino
serPort = "/dev/ttyUSB0"
baudRate = 9600
ser = None

# Get the previous port setting that was successful
try:
    port = int(addon.getSetting("clock_port"))
except Exception as e:
    port = 1

# Loop around the ports trying to find a serial interface
MAX_PORT = 9
for i in range(MAX_PORT):
    try:
        ser = serial.Serial(port='COM'+str(port), baudrate=baudRate)
        infoTrace("clocksync.py", "Opened COM" + str(port) + " to use with Arduino")
        addon = xbmcaddon.Addon("service.zomboided.tools")
        addon.setSetting("clock_port", str(port))
        break
    except Exception as e:
        debugTrace("Couldn't open COM" + str(port) + " to use with Arduino")
        ser = None
    port += 1
    if port > MAX_PORT: port = 1


startMarker = 60    # <
endMarker = 62      # >

# Send some messages if a serial interface is established
if not ser == None :
    infoTrace("clocksync.py", "Communicating with Arduino clock")
    error = False
    msg = ""
    
    # Wait for the Arduino to proclaim itself ready
    if not error:
        if getMessageFromArduino("Ready", 30) != None:
            debugTrace("Arduino is ready to receive data")
            time.sleep(1)
        else:
            error = True
            msg = "Arduino not ready"
    
    # Arduino should ask whether it should display 12 or 24 hour clock
    if not error:
        if getMessageFromArduino("Display", 10) != None:
            debugTrace("Arduino asked if it's 12/24 hour display")
            time.sleep(1)
            clock_display = addon.getSetting("clock_display")
            if clock_display == "24":            
                sendToArduino("<24>")
            else:
                sendToArduino("<12>")
        else:
            error = True
            msg = "Expected 'Display' request but didn't get it"
        
    # If the Arduino asks for the time, send it back
    if not error: 
        if getMessageFromArduino("Time", 10) != None:
            debugTrace("Arduino asked for the time")
            time.sleep(1)
            sendToArduino("<" + getYYMMDDwHHMMSS() + ">")
        else:
            error = True
            msg = "Expected 'Time' request but didn't get it"
            
    # Arduino should send a Thanks when it has a good time and program can exit
    if not error: 
        if getMessageFromArduino("Thanks", 30) != None:
            infoTrace("clocksync.py", "Arduino has what it needs")
        else:
            error = True
            msg = "Expecting 'Thanks' response but didn't get it"
    
    # Output a message if an error happened
    if error:
        errorTrace("clocksync.py", msg)
        if show_dialog: xbmcgui.Dialog().ok(addon_name, msg)

    ser.close
else:
    if show_dialog: xbmcgui.Dialog().ok(addon_name, "Couldn't find Arduino clock")

debugTrace("-- Exit clocksync.py --")
