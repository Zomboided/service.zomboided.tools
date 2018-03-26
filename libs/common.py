#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2016 Zomboided
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#    Shared code fragments

import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui
from glob import glob
from libs.utility import debugTrace, errorTrace, infoTrace, newPrint, now


SLEEP_DELAY_TIME = 10
SLEEP_OFF = "Off"
SLEEP_END = "End"


def getKeyMapsPath(path):
    return xbmc.translatePath("special://userdata/keymaps/" + path)
    

def getKeyMapsFileName():
    return "zomboided.xml"
    
    
def fixKeymaps():
    # Fix the keymap file name if it's been changed or the old name was being used
    name = getKeyMapsFileName()
    dir = getKeyMapsPath("*")
    full_name = getKeyMapsPath(name)
    try:
        debugTrace("Getting contents of keymaps directory " + dir)
        files = (glob(dir))
        if not full_name in files and len(files) > 0:
            for file in files:
                if (name in file):
                    infoTrace("common.py", "Renaming " + file + " to " + full_name)
                    xbmcvfs.rename(file, full_name)
                    xbmc.sleep(100)
                    # Wait 10 seconds for rename to happen otherwise quit and let it fail in the future
                    for i in range(0, 9):
                        if xbmcvfs.exists(full_name): break
                        xbmc.sleep(1000)
                    return True
    except Exception as e:
        errorTrace("common.py", "Problem fixing the keymap filename.")
        errorTrace("common.py", str(e))
    return False
    
    
def forceSleepLock():
    # Loop until we get the lock, or have waited for 10 seconds
    i = 0
    while i < 10 and not xbmcgui.Window(10000).getProperty("ZTools_Sleep_Lock") == "":
        xbmc.sleep(1000)
        i = i + 1
    xbmcgui.Window(10000).setProperty("ZTools_Sleep_Lock", "Forced Locked")
    
    
def getSleepLock():
    # If the lock is forced, don't wait, just return (ie don't queue)
    if xbmcgui.Window(10000).getProperty("ZTools_Sleep_Lock") == "Forced Locked" : return False
    # If there's already a queue on the lock, don't wait, just return
    if not xbmcgui.Window(10000).getProperty("ZTools_Sleep_Lock_Queued") == "" : return False
    # Loop until we get the lock or time out after 5 seconds
    xbmcgui.Window(10000).setProperty("ZTools_Sleep_Lock_Queued", "Queued")
    i = 0
    while i < 5 and not xbmcgui.Window(10000).getProperty("ZTools_Sleep_Lock") == "":
        xbmc.sleep(1000)
        i = i + 1
    # Free the queue so another call can wait on it
    xbmcgui.Window(10000).setProperty("ZTools_Sleep_Lock_Queued", "")   
    # Return false if a forced lock happened whilst we were queuing
    if xbmcgui.Window(10000).getProperty("ZTools_Sleep_Lock") == "Forced Locked" : return False
    # Return false if the lock wasn't obtained because of a time out
    if i == 5 : return False 
    xbmcgui.Window(10000).setProperty("ZTools_Sleep_Lock", "Locked")
    return True

    
def freeSleepLock():
    xbmcgui.Window(10000).setProperty("ZTools_Sleep_Lock", "")    

    
def requestSleep():

    # Don't know where this was called from so using plugin name to get addon handle
    addon = xbmcaddon.Addon("service.zomboided.tools")
    addon_name = addon.getAddonInfo("name")

    # Don't sleep if we can't get a lock
    if getSleepLock():
        t = now()
        remain = getSleepRemaining()
        if t - getSleepReqTime() < SLEEP_DELAY_TIME:
            # The last time sleep was requested was very recently so move to next value
            current = getSleepReq()
            if current == "": current = getSleep()            
            if current == SLEEP_OFF:
                current = "End"
            elif current == SLEEP_END:
                current = addon.getSetting("sleep_inc")
            elif current.isdigit():
                current_int = int(current)
                if getSleepReq() == "" and remain.isdigit():
                    # This deals with the case where a timer is running already
                    current_int = int(remain)
                sleep_max = int(addon.getSetting("sleep_max"))
                sleep_inc = int(addon.getSetting("sleep_inc"))
                if current_int >= sleep_max:
                    current = SLEEP_OFF                    
                else:
                    if current_int + sleep_inc > sleep_max:
                        current = addon.getSetting("sleep_max")
                    else:
                        current = str(((current_int / sleep_inc) + 1) * sleep_inc)
            else:
                current == SLEEP_OFF
            setSleepReq(current)
            debugTrace("Repeat sleep request, " + current + ", remain is " + "")
        else:
            # Otherwise get the value of the current sleep state and display it
            if remain == "":
                current = getSleep()
            else:
                current = remain
            debugTrace("New sleep request, " + current + ", remain is " + "")
        
        if current.isdigit():
            xbmcgui.Dialog().notification("Sleeping in " + current + " minutes." , "", "", 2000, False)
        else:
            if current == SLEEP_END:
                xbmcgui.Dialog().notification("Sleeping after end of current video." , "", "", 2000, False)
            else:
                xbmcgui.Dialog().notification("Sleep is off." , "", "", 2000, False)
        
        addAlert()
        setSleepReqTime(t)
        xbmc.sleep(1000)
        freeSleepLock()
                    

def getSleep():
    s = xbmcgui.Window(10000).getProperty("ZTools_Sleep")
    if s == "": return SLEEP_OFF
    else: return s

    
def setSleep(value):
    xbmcgui.Window(10000).setProperty("ZTools_Sleep", value)


def getSleepReq():
    return xbmcgui.Window(10000).getProperty("ZTools_Sleep_Request")

    
def setSleepReq(value):
    xbmcgui.Window(10000).setProperty("ZTools_Sleep_Request", value)


def getSleepReqTime():
    s = xbmcgui.Window(10000).getProperty("ZTools_Sleep_Request_Time")
    if s == "": return 0
    else: return int(s)

        
def setSleepReqTime(value):
    xbmcgui.Window(10000).setProperty("ZTools_Sleep_Request_Time", str(value))
    

def getSleepRemaining():
    return xbmcgui.Window(10000).getProperty("ZTools_Sleep_Remaining")

    
def setSleepRemaining(value):
    xbmcgui.Window(10000).setProperty("ZTools_Sleep_Remaining", value)


def addAlert():
    xbmcgui.Window(10000).setProperty("ZTools_Alert", "Updated")

    
def clearAlert():
    xbmcgui.Window(10000).setProperty("ZTools_Alert", "")

    
def activeAlert():
    if not xbmcgui.Window(10000).getProperty("ZTools_Alert") == "":
        return True
    else:
        return False
        
        
def clearSleep():
    setSleep(SLEEP_OFF)
    setSleepRemaining("")
    clearAlert()
    freeSleepLock()
    

    
    
    
    