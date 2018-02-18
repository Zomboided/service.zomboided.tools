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
from libs.vpnapi import VPNAPI

def clearCache(window, dialogs):
    addon = xbmcaddon.Addon("service.zomboided.tools")
    addon_name = addon.getAddonInfo("name")

    caches = []
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.covenant)"): caches.append("covenant")
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.exodus)"): caches.append("exodus")
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.fantastic)"): caches.append("fantastic")
    
    list = ""
    for name in caches:
        newPrint("Name is " + name)
        if list == "": list = name.title()
        else: list = list + ", " + name.title()
        
    try:
        commDelay = int(addon.getSetting("cache_command_delay"))*1000
    except:
        commDelay = 10000

    if len(caches) > 0 and (not dialogs or xbmcgui.Dialog().yesno(addon_name, "Clear the video caches for " + list + "? [B]You must avoid any input[/B] until the process is finished.\nAre you sure you want to continue?")):

        progDiag = xbmcgui.DialogProgressBG()
        progDiag.create("Clearing Caches", "[B]Avoid any input![/B]")
        progDiag.update(0)
    
        api = None
        if xbmc.getCondVisibility("System.HasAddon(service.vpn.manager)"):
            try:
                api = VPNAPI()
            except Exception as e:
                errorTrace("service.py", "Couldn't connect to the VPN Mgr API")
                errorTrace("service.py", str(e))
                api = None        
            
        cleared = 0

        # Pause the VPN filtering here so there's ample time for the filtering to stop
        if not api == None: 
            api.pause()
        xbmc.sleep(commDelay)
        
        percent = 0
        percent_inc = (100/len(caches))/4   
        # number of addons to clear divided by number of operations in each addon

        if not api == None:
            # This is just an info message, the VPN was paused earlier
            progDiag.update(percent, "Pausing VPN filtering")
            xbmc.sleep(commDelay)

        # Stop any media playing
        player = xbmc.Player()
        if player.isPlaying():
            infoTrace("cache.py", "Stopping media to clear caches")
            player.stop()
            
        # Change the window and stop any media
        if not window == 0:
            s = "ActivateWindow(" + str(window) + ")"
            xbmc.executebuiltin(s)
            xbmc.sleep(commDelay)
        
        for i in caches:
            name = i
            tname = name.title()       
            try:
                # Clear the cache
                percent = percent + percent_inc      
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
                percent = percent + percent_inc       
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
                percent = percent + percent_inc     
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
                    xbmc.sleep(commDelay*3)
                    xbmc.executebuiltin("Action(Back)")
                    xbmc.sleep(commDelay)
                    xbmc.executebuiltin("Action(Back)")
                    xbmc.sleep(commDelay)
                    cleared += 1
                else:
                    progDiag.update(percent, "Skipping " + tname + " Trakt TV collection")
                    xbmc.sleep(1000)
                    
                # Refresh the movie collection list
                percent = percent + percent_inc
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
                    xbmc.sleep(commDelay*3)
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

        # Restart the filtering
        if not api == None: 
            progDiag.update(percent, "Restarting VPN filtering")
            api.restart()
            xbmc.sleep(commDelay)

        if cleared > 0:
            progDiag.update(100, "Finished clearing selected caches", " ")
        else:
            progDiag.update(100, "No caches were cleared", " ")
        xbmc.sleep(2000)        
                
        progDiag.close() 
        xbmc.sleep(1000)

    
def resetEmby(window, dialogs):

    addon = xbmcaddon.Addon("service.zomboided.tools")
    addon_name = addon.getAddonInfo("name")

    if xbmc.getCondVisibility("System.HasAddon(plugin.video.emby)"):

        try:
            commDelay = int(addon.getSetting("cache_command_delay"))*1000
        except:
            commDelay = 10000

        progDiag = xbmcgui.DialogProgressBG()
        progDiag.create("Resetting Emby database", "[B]Avoid any input![/B]")
        progDiag.update(0)
        xbmc.sleep(2000)

        # Change the window and stop any media
        if not window == 0:
            player = xbmc.Player()
            if player.isPlaying():
                infoTrace("cache.py", "Stopping media to reset Emby database")
                player.stop()
            s = "ActivateWindow(" + str(window) + ")"
            xbmc.executebuiltin(s)
            xbmc.sleep(commDelay)

        progDiag.update(10, "Resetting Emby database")
        infoTrace("cache.py", "Resetting Emby databases")
        command = "ActivateWindow(10025,plugin://plugin.video.emby/?mode=repair,return)"
        xbmc.executebuiltin(command)
        xbmc.sleep(commDelay)
        xbmc.executebuiltin("Action(Select)")
        xbmc.sleep(commDelay)
        xbmc.executebuiltin("Action(Back)")
        xbmc.sleep(commDelay)
    
        progDiag.update(100, "Initiated reset of Emby database", "Emby will report the progress")
        xbmc.sleep(3000)
            
    else:
        progDiag.update(100, "Emby is not available, cannot reset database")
        xbmc.sleep(1000)        
    
    progDiag.close() 
    xbmc.sleep(1000)
