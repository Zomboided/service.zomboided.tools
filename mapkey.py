#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2018 Zomboided
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
#    This module allows the user to bind a key to one of the operations
#    that can be performed within Zomboided Tools

import xbmc
from xbmcgui import Dialog, WindowXMLDialog,DialogProgress
import xbmcgui
import xbmcaddon
import xbmcvfs
import os
from glob import glob
from threading import Timer
from libs.utility import debugTrace, errorTrace, infoTrace, newPrint
from libs.common import fixKeymaps, getKeyMapsPath, getKeyMapsFileName, getSleepLock, freeSleepLock, clearSleep


class KeyListener(WindowXMLDialog):
    TIMEOUT = 5

    def __new__(cls):
        gui_api = tuple(map(int, xbmcaddon.Addon('xbmc.gui').getAddonInfo('version').split('.')))
        file_name = "DialogNotification.xml" if gui_api >= (5, 11, 0) else "DialogKaiToast.xml"
        return super(KeyListener, cls).__new__(cls, file_name, "")
        
    def __init__(self):
        self.key = None

    def onInit(self):
        self.getControl(400).setImage(xbmc.translatePath("special://home/addons/service.zomboided.tools/resources/map.png"))
        self.getControl(401).addLabel(xbmcaddon.Addon("service.zomboided.tools").getAddonInfo("name"))
        self.getControl(402).addLabel("Press a key to map or wait to clear.")

    def onAction(self, action):
        code = action.getButtonCode()
        self.key = None if code == 0 else str(code)
        self.close()
        
    @staticmethod
    def record_key():
        dialog = KeyListener()
        timeout = Timer(KeyListener.TIMEOUT, dialog.close)
        timeout.start()
        dialog.doModal()
        timeout.cancel()
        key = dialog.key
        del dialog
        if key == None: return ""
        return key
        
        
addon = xbmcaddon.Addon("service.zomboided.tools")
addon_name = addon.getAddonInfo("name")

action = sys.argv[1]

debugTrace("-- Entered mapkey.py with parameter " + action + " --")

sleep_key = ""

map_name = getKeyMapsFileName()
xml_start = '<keymap><global><keyboard>\n'
xml_key = '<key id="#KEY">runscript(#PATH#COMMAND)</key>\n'
xml_long = '<key id="#KEY" mod="longpress">runscript(#PATH#COMMAND)</key>\n'
xml_end = '</keyboard></global></keymap>\n'
sleep_command = "sleep.py"


# Fix the keymap if it's been renamed by the Keymap addon
fixKeymaps()

lines = []

# Read any existing keymap and the keys we're interested in
if xbmcvfs.exists(getKeyMapsPath(map_name)):
    path = getKeyMapsPath(map_name)    
    try:
        debugTrace("Writing the map file to " + path)
        map_file = open(path, 'r')
        lines = map_file.readlines()
        map_file.close()
        i = 0
        for line in lines:
            if sleep_command in line:
                i1 = line.index("key id=\"") + 8
                i2 = line.index("\"", i1)
                sleep_key = line[i1:i2]
                debugTrace("Found sleep key " + sleep_key)
                lines[i] = ""
            i = i + 1
    except Exception as e:
        errorTrace("mapkey.py", map_name + " is malformed")
        errorTrace("mapkey.py", str(e))
        lines = []


# If there is no keymap, create a blank one with start and end tags
if len(lines) == 0:
    lines.append(xml_start)
    lines.append(xml_end)

if getSleepLock():

    clearSleep()

    # Get the updated keys
    if action == "sleep":
        if sleep_key == "": 
            msg = "Do you want to map a key or remote button to the sleep function?"
            y = "No"
            n = "Yes"
        else: 
            msg = "Key ID " + sleep_key + " is mapped to the sleep function.  Remap or clear current mapping?"
            y = "Clear"
            n = "Remap"
        if not xbmcgui.Dialog().yesno(addon_name, msg, "", "", n, y):
            sleep_key = KeyListener().record_key()
            if sleep_key == "": 
                dialog = "Sleep is not mapped to a key."
                icon = "/resources/unmapped.png"
            else: 
                dialog = "Sleep is mapped to key ID " + sleep_key + "."
                icon = "/resources/mapped.png"
            xbmcgui.Dialog().notification(addon_name, dialog, xbmc.translatePath("special://home/addons/service.zomboided.tools/" + icon), 5000, False)
        else:
            if not sleep_key == "": 
                sleep_key = ""

    # Add the keys to the start of the keymap file
    if not sleep_key == "":
        out = xml_key.replace("#KEY", sleep_key)
        out = out.replace("#PATH", xbmc.translatePath("special://home/addons/service.zomboided.tools/"))
        out = out.replace("#COMMAND", sleep_command)
        lines.insert(1, out)

    # Count the number of valid lines to write out
    i = 0
    for line in lines:
        if not line == "": i += 1
    
    try:    
        path = getKeyMapsPath(map_name)
        if i == 2:
            # Delete keymap file, it's empty apart from the start and end tags
            if xbmcvfs.exists(path):
                debugTrace("No key mappings so deleting the map file " + path)            
                xbmcvfs.delete(path)
                xbmcgui.Dialog().ok(addon_name, "Keymap has been removed as no keys have been mapped.  You must restart for these changes to take effect.")
            else:
                debugTrace("No key mappings so not creating a map file")
        else:
            # Write the updated keymap
            path = getKeyMapsPath(map_name)
            map_file = open(path, 'w')
            for line in lines:
                if not line == "": map_file.write(line)    
            map_file.close()
            xbmcgui.Dialog().ok(addon_name, "Keymap has been updated.  You must restart for these changes to take effect.")
    except Exception as e:
        errorTrace("mapkey.py", "Couldn't update keymap file " + path)
        errorTrace("mapkey.py", str(e))
        xbmcgui.Dialog().ok(addon_name, "Problem updating the keymap file, check error log.")
        
    # Warn the user if maps could clash
    path = getKeyMapsPath("*.xml")
    try:
        debugTrace("Getting contents of keymaps directory " + path)
        files = (glob(path))
        if len(files) > 1:
            xbmcgui.Dialog().ok(addon_name, "Other keymaps exist and are applied in alphabetical order.  If your mappings don't work then it could be that they're being over written by another map.")
            infoTrace("mapkey.py", "Multiple (" + str(len(files)) + ") keymaps, including " + map_name + " detected in " + getKeyMapsPath(""))
    except Exception as e:
        errorTrace("import.py", "Couldn't check to see if other keymaps were clashing")
        errorTrace("import.py", str(e))

freeSleepLock()

xbmc.executebuiltin("Addon.OpenSettings(service.zomboided.tools)")

debugTrace("-- Exit mapkey.py --")