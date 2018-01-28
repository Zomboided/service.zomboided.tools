#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2017 Zomboided
#
#    Connection script called by the VPN Manager for OpenVPN settings screen
#    to validate a connection to a VPN provider.
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
#    This module is a bunch of functions that are called from the settings
#    menu to manage various files groups.

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import datetime
import os
from libs.utility import debugTrace, errorTrace, infoTrace, newPrint

addon = xbmcaddon.Addon("service.zomboided.tools")
addon_name = addon.getAddonInfo("name")

action = sys.argv[1]

debugTrace("-- Entered managefiles.py with parameter " + action + " --")
        
# Copy the log file        
if action == "log":
    log_path = ""
    dest_path = ""
    try:
        log_path = xbmc.translatePath("special://logpath/kodi.log")
        start_dir = ""
        dest_folder = xbmcgui.Dialog().browse(0, "Select folder to copy log file into", "files", "", False, False, start_dir, False)
        dest_path = "kodi " + datetime.datetime.now().strftime("%y-%m-%d %H-%M-%S") + ".log"
        dest_path = dest_folder + dest_path.replace(" ", "_")
        debugTrace("Copying " + log_path + " to " + dest_path)
        addon = xbmcaddon.Addon("service.zomboided.tools")
        infoTrace("managefiles.py", "Copying log file to " + dest_path + ".  Using version " + addon.getSetting("version_number"))
        xbmcvfs.copy(log_path, dest_path)
        if not xbmcvfs.exists(dest_path): raise IOError('Failed to copy log ' + log_path + " to " + dest_path)
        dialog_message = "Copied log file to:\n" + dest_path
    except:
        errorTrace("managefiles.py", "Failed to copy log from " + log_path + " to " + dest_path)
        if xbmcvfs.exists(log_path):
            dialog_message = "Error copying log, try copying it to a different location."
        else:
            dialog_messsage = "Could not find the kodi.log file."
        errorTrace("managefiles.py", dialog_message + " " + log_path + ", " + dest_path)
    xbmcgui.Dialog().ok("Log Copy", dialog_message)


xbmc.executebuiltin("Addon.OpenSettings(service.zomboided.tools)")    
    
debugTrace("-- Exit managefiles.py --")
