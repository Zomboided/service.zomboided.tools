#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2017 Zomboided
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
#    This module displays the Zomboided Tools menu options

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
import os
from libs.utility import debugTrace, errorTrace, infoTrace
from libs.logbox import popupKodiLog
from libs.speedtest import speedTest
from libs.managefiles import copyLog
from libs.common import getIconPath

debugTrace("-- Entered addon.py " + sys.argv[0] + " " + sys.argv[1] + " " + sys.argv[2] + " --")

# Set the addon name for use in the dialogs
addon = xbmcaddon.Addon()
addon_name = addon.getAddonInfo("name")

# Get the arguments passed in
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = sys.argv[2].split("?", )
action = ""
params = ""
# If an argument has been passed in, the first character will be a ?, so the first list element is empty
inc = 0
for token in args:
    if inc == 1 : action = token
    if inc > 1 : params = params + token
    inc = inc + 1  

debugTrace("Parsed arguments to action=" + action + " params=" + params)
    
def topLevel():
    # Build the top level menu with URL callbacks to this plugin
    debugTrace("Displaying the top level menu")
    url = base_url + "?settings"
    li = xbmcgui.ListItem("Add-on Settings")
    li.setArt({"icon":getIconPath()+"box.png"})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
    url = base_url + "?viewlog"
    li = xbmcgui.ListItem("View Log")
    li.setArt({"icon":getIconPath()+"box.png"})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
    url = base_url + "?copylog"
    li = xbmcgui.ListItem("Copy Log")
    li.setArt({"icon":getIconPath()+"box.png"})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
    url = base_url + "?speedtest"
    li = xbmcgui.ListItem("LAN Speed Test")
    li.setArt({"icon":getIconPath()+"box.png"})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
    xbmcplugin.endOfDirectory(addon_handle)
    return
    

def back():
    xbmc.executebuiltin("Action(ParentDir)")
    return
    

if action == "settings" :
    debugTrace("Opening settings")
    xbmc.executebuiltin("Addon.OpenSettings(service.zomboided.tools)")    
elif action == "viewlog" :
    debugTrace("Displaying log")
    popupKodiLog()
elif action == "copylog" :
    debugTrace("Copying log")
    copyLog()
elif action == "speedtest" :
    debugTrace("Displaying log")
    speedTest()    
else: topLevel()


debugTrace("-- Exit addon.py --")    