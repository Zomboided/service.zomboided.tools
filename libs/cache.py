#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2017 Zomboided
#
#    Clear a bunch of caches using the best interfaces available
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
from libs.utility import debugTrace, errorTrace, infoTrace, newPrint

def clearCache(window):
    addon = xbmcaddon.Addon("service.zomboided.tools")
    addon_name = addon.getAddonInfo("name")

    COMM_DELAY = 5000

    cleared = 0

    # Change the window and stop any media
    if not window == 0:
        player = xbmc.Player()
        if player.isPlaying():
            infoTrace("clearcache.py", "Stopping media to clear caches")
            player.stop()
        s = "ActivateWindow(" + str(window) + ")"
        xbmc.executebuiltin(s)
        xbmcgui.Dialog().notification(addon_name, "Looking for caches to clear", xbmcgui.NOTIFICATION_INFO, 5000, False)
        xbmc.sleep(COMM_DELAY)
    
    # Clear Covenant cache and providers        
    try:
        if xbmc.getCondVisibility("System.HasAddon(plugin.video.covenant)"):
            infoTrace("clearcache.py", "Clearing Covenant cache")
            xbmcgui.Dialog().notification(addon_name, "Clearing Covenant cache, please wait", xbmcgui.NOTIFICATION_WARNING, 5000, False)
            xbmc.executebuiltin("ActivateWindow(10025,plugin://plugin.video.covenant/?action=clearCache,return)")
            xbmc.sleep(COMM_DELAY)
            xbmc.executebuiltin("Action(Left)")
            xbmc.sleep(COMM_DELAY)
            xbmc.executebuiltin("Action(Select)")
            xbmc.sleep(COMM_DELAY)
            xbmc.executebuiltin("Action(Back)")
            xbmc.sleep(COMM_DELAY)
            xbmcgui.Dialog().notification(addon_name, "Clearing Covenant providers, please wait", xbmcgui.NOTIFICATION_WARNING, 5000, False)
            infoTrace("clearcache.py", "Clearing Covenant providers")
            xbmc.executebuiltin("ActivateWindow(10025,plugin://plugin.video.covenant/?action=clearSources,return)")
            xbmc.sleep(COMM_DELAY)
            xbmc.executebuiltin("Action(Left)")
            xbmc.sleep(COMM_DELAY)
            xbmc.executebuiltin("Action(Select)")
            xbmc.sleep(COMM_DELAY)
            xbmc.executebuiltin("Action(Back)")
            xbmc.sleep(COMM_DELAY)
            cleared += 1
        else:
            debugTrace("Covenant not installed and enabled, can't clear cache and providers")
    except Exception as e:
        errorTrace("clearcache.py", "Problem clearing Covenant caches")
        errorTrace("clearcache.py", str(e))

    # Clear Fantastic cache and providers        
    try:
        if xbmc.getCondVisibility("System.HasAddon(plugin.video.fantastic)"):
            infoTrace("clearcache.py", "Clearing Fantastic cache")
            xbmcgui.Dialog().notification(addon_name, "Clearing Fantastic cache, please wait", xbmcgui.NOTIFICATION_WARNING, 5000, False)
            xbmc.executebuiltin("ActivateWindow(10025,plugin://plugin.video.fantastic/?action=clearCache,return)")
            xbmc.sleep(COMM_DELAY)
            xbmc.executebuiltin("Action(Left)")
            xbmc.sleep(COMM_DELAY)
            xbmc.executebuiltin("Action(Select)")
            xbmc.sleep(COMM_DELAY)
            xbmc.executebuiltin("Action(Back)")
            xbmc.sleep(COMM_DELAY)
            xbmcgui.Dialog().notification(addon_name, "Clearing Fantastic providers, please wait", xbmcgui.NOTIFICATION_WARNING, 5000, False)
            infoTrace("clearcache.py", "Clearing Fantastic providers")
            xbmc.executebuiltin("ActivateWindow(10025,plugin://plugin.video.fantastic/?action=clearSources,return)")
            xbmc.sleep(COMM_DELAY)
            xbmc.executebuiltin("Action(Left)")
            xbmc.sleep(COMM_DELAY)
            xbmc.executebuiltin("Action(Select)")
            xbmc.sleep(COMM_DELAY)
            xbmc.executebuiltin("Action(Back)")
            xbmc.sleep(COMM_DELAY)
            cleared += 1
        else:
            debugTrace("Fantastic not installed and enabled, can't clear cache and providers")
    except Exception as e:
        errorTrace("clearcache.py", "Problem clearing Fantastic caches")
        errorTrace("clearcache.py", str(e))    

    if cleared == 0:    
        xbmcgui.Dialog().notification(addon_name, "No caches were found to clear", xbmcgui.NOTIFICATION_ERROR, 5000, False)
    else:
        xbmcgui.Dialog().notification(addon_name, "Finished clearing the caches", xbmcgui.NOTIFICATION_INFO, 5000, False)
