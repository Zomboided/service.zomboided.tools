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

    caches = []
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.covenant)"): caches.append("covenant")
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.exodus)"): caches.append("exodus")
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.fantastic)"): caches.append("fantastic")

    try:
        commDelay = int(addon.getSetting(cache_command_delay))
    except:
        commDelay = 5000

    cleared = 0

    progDiag = xbmcgui.DialogProgressBG()
    progDiag.create("Clearing Caches", "[B]Avoid any input![/B]")
    progDiag.update(0)
    
    percent = 0
    percentJump = (100/len(caches))/4
    
    # Change the window and stop any media
    if not window == 0:
        player = xbmc.Player()
        if player.isPlaying():
            infoTrace("cache.py", "Stopping media to clear caches")
            player.stop()
        s = "ActivateWindow(" + str(window) + ")"
        xbmc.executebuiltin(s)
        xbmc.sleep(commDelay)
    
    for i in caches:
        name = i
        tname = name.title()       
        try:
            # Clear the cache
            percent = percent + percentJump      
            if addon.getSetting(name + "_cache") == "true":
                progDiag.update(percent, "Clearing " + tname + " cache")
                infoTrace("cache.py", "Clearing " + tname + " cache")
                command = "ActivateWindow(10025,plugin://plugin.video." + name + "/?action=clearCache,return)"
                xbmc.executebuiltin(command)
                xbmc.sleep(commDelay)
                xbmc.executebuiltin("Action(Left)")
                xbmc.sleep(commDelay)
                xbmc.executebuiltin("Action(Select)")
                xbmc.sleep(commDelay)
                xbmc.executebuiltin("Action(Back)")
                xbmc.sleep(commDelay)
                cleared += 1
            else:
                progDiag.update(percent, "Skipping " + tname + " cache")
                xbmc.sleep(1000)

            # Clear the providers                
            percent = percent + percentJump       
            if addon.getSetting(name + "_providers") == "true":
                progDiag.update(percent, "Clearing " + tname + " providers")
                infoTrace("cache.py", "Clearing " + tname + " providers")
                command = "ActivateWindow(10025,plugin://plugin.video." + name + "/?action=clearSources,return)"
                xbmc.executebuiltin(command)
                xbmc.sleep(commDelay)
                xbmc.executebuiltin("Action(Left)")
                xbmc.sleep(commDelay)
                xbmc.executebuiltin("Action(Select)")
                xbmc.sleep(commDelay)
                xbmc.executebuiltin("Action(Back)")
                xbmc.sleep(commDelay)               
                cleared += 1
            else:
                progDiag.update(percent, "Skipping " + tname + " providers")
                xbmc.sleep(1000)
                
            # Refresh the TV collection list
            percent = percent + percentJump     
            if addon.getSetting(name + "_tv_collection") == "true":
                progDiag.update(percent, "Refreshing " + tname + " Trakt TV collection") 
                infoTrace("cache.py", "Refreshing " + tname + " Trakt TV collection")                
                command = "ActivateWindow(10025,plugin://plugin.video." + name + "/?action=mytvNavigator,return)"
                xbmc.executebuiltin(command)
                xbmc.sleep(commDelay)
                xbmc.executebuiltin("Action(PageUp)")
                xbmc.sleep(commDelay)
                xbmc.executebuiltin("Action(Down)")
                xbmc.sleep(commDelay)
                xbmc.executebuiltin("Action(Select)")
                xbmc.sleep(commDelay)
                xbmc.executebuiltin("Action(Back)")
                xbmc.sleep(commDelay)
                xbmc.executebuiltin("Action(Back)")
                xbmc.sleep(commDelay)
                cleared += 1
            else:
                progDiag.update(percent, "Skipping " + tname + " Trakt TV collection")
                xbmc.sleep(1000)
                
            # Refresh the movie collection list
            percent = percent + percentJump
            if addon.getSetting(name + "_movie_collection") == "true":
                progDiag.update(percent, "Refreshing " + tname + " Trakt movie collection")
                infoTrace("cache.py", "Refreshing " + tname + " Trakt TV collection")                
                command = "ActivateWindow(10025,plugin://plugin.video." + name + "/?action=mymovieNavigator,return)"
                xbmc.executebuiltin(command)
                xbmc.sleep(commDelay)
                xbmc.executebuiltin("Action(PageUp)")
                xbmc.sleep(commDelay)
                xbmc.executebuiltin("Action(Down)")
                xbmc.sleep(commDelay)
                xbmc.executebuiltin("Action(Select)")
                xbmc.sleep(commDelay)
                xbmc.executebuiltin("Action(Back)")
                xbmc.sleep(commDelay)
                xbmc.executebuiltin("Action(Back)")
                xbmc.sleep(commDelay)                 
                cleared += 1
            else:
                progDiag.update(percent, "Skipping " + tname + " Trakt movie collection")
                xbmc.sleep(1000)
                
        except Exception as e:
            errorTrace("cache.py", "Problem clearing " + tname + " caches")
            errorTrace("cache.py", str(e))    

    if cleared > 0:
        progDiag.update(100, "Finished clearing selected caches", " ")
    else:
        progDiag.update(100, "No caches were cleared", " ")
    xbmc.sleep(2000)        
            
    progDiag.close() 
