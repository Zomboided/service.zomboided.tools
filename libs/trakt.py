#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2018 Zomboided
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
#    This module updates Trakt keys

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
from libs.utility import debugTrace, errorTrace, infoTrace, newPrint


def getAddons():
    addons = []
    files = []
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.covenant)"): 
        addons.append("Covenant")
        files.append(xbmc.translatePath("special://home/addons/script.module.covenant/lib/resources/lib/modules/trakt.py"))
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.exodus)"):
        addons.append("Exodus")
        files.append(xbmc.translatePath("special://home/addons/script.module.exodus/lib/resources/lib/modules/trakt.py"))
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.fantastic)"):
        addons.append("Fantastic")
        files.append(xbmc.translatePath("special://home/addons/script.module.fantastic/lib/resources/lib/modules/trakt.py"))
    return addons, files


def updateTrakt(window, dialogs):
    addon = xbmcaddon.Addon("service.zomboided.tools")
    addon_name = addon.getAddonInfo("name")

    addons, files = getAddons()
    
    list = ""
    if len(addons) > 0:
        i = 0
        for name in addons:
            if i == 0: list = name
            else: list = list + ", " + name
            i += 1
        
    try:
        commDelay = int(addon.getSetting(cache_command_delay))
    except:
        commDelay = 5000
    
    if len(addons) > 0 and (not dialogs or xbmcgui.Dialog().yesno(addon_name, "Modify some add-ons to use a custom Trakt ID and secret. You can get these by logging onto Trakt and creating an app at https://trakt.tv/oauth/applications.\nAre you sure you want to continue?")):
        
        percent = 0       
        progDiag = xbmcgui.DialogProgress()
        progDiag.create(addon_name, "Modifying Trakt tokens for " + list + ".","Stopping any playing media.")
        progDiag.update(percent)
        percent_inc = (90/len(files))   

        # Change the window and stop any media
        player = xbmc.Player()
        if player.isPlaying():
            infoTrace("trakt.py", "Stopping media")
            player.stop()
        if not window == 0:
            s = "ActivateWindow(" + str(window) + ")"
            xbmc.executebuiltin(s)
            xbmc.sleep(commDelay)

        # Get the new Trakt tokens to be used
        trakt_path = xbmc.translatePath("special://userdata/addon_data/service.zomboided.tools/TRAKT.txt")
        if xbmcvfs.exists(trakt_path):
            infoTrace("trakt.py", "TRAKT.txt found in userdata, getting ID and secret from it.")
            try:
                trakt_file = open(trakt_path, 'r')
                trakt = trakt_file.readlines()
                trakt_file.close()
                if len(trakt) == 2:
                    trakt_id = trakt[0].strip(' \t\n\r')
                    addon.setSetting("trakt_id", trakt_id)
                    trakt_secret = trakt[1].strip(' \t\n\r')
                    addon.setSetting("trakt_secret", trakt_secret)  
                else:
                    raise Exception("Trakt file was malformed, should be just 2 lines with an ID and a line with a secret")
            except Exception as e:
                errorTrace("common.py", "TRAKT.txt found in userdata, but file appears to be invalid.")
                errorTrace("trakt.py", str(e))
            addon = xbmcaddon.Addon("service.zomboided.tools")
        new_trakt_id = addon.getSetting("trakt_id")
        new_trakt_secret = addon.getSetting("trakt_secret")      
        
        updated = 0
        percent = 10
        if new_trakt_id == "" or new_trakt_secret == "":
            progDiag.update(100, "No Trakt tokens were supplied.","Enter these in the Settings and try again.")
            sleep(3000)
        else:
            i = 0
            for name in addons:
                trakt_path = files[i]
                trakt_path_old = trakt_path + ".old"
                try:                    
                    progDiag.update(percent, "Modifying " + name + " with new Trakt tokens.","Please wait.")
                    updated += 1
                    if xbmcvfs.exists(trakt_path):
                        debugTrace("Attempted to update " + trakt_path)
                        # Read existing trakt module
                        trakt_file = open(trakt_path, 'r')
                        trakt = trakt_file.readlines()
                        trakt_file.close()
                        # Rename existing module if it doesn't already exist
                        if not xbmcvfs.exists(trakt_path_old):
                            xbmcvfs.rename(trakt_path, trakt_path_old)  
                        # Write out new module
                        trakt_file = open(trakt_path, 'w')
                        modified = False
                        mod_flag = "# Modified by ZTools"
                        for line in trakt:
                            if line.startswith(mod_flag):
                                modified = True
                                debugTrace("Found the mod flag, have updated this previously")
                            if line.startswith("V2_API_KEY"):
                                if not modified : 
                                    trakt_file.write(mod_flag + "\n")
                                    trakt_file.write("#" + line)
                                trakt_file.write("V2_API_KEY = '" + trakt_id + "'\n")
                            elif line.startswith("CLIENT_SECRET"):
                                if not modified:
                                    trakt_file.write("#" + line)
                                trakt_file.write("CLIENT_SECRET = '" + trakt_secret + "'\n")
                            else:
                                trakt_file.write(line)
                        trakt_file.close()
                    else:
                        errorTrace("trakt.py", "Couldn't fine trakt module for " + name)
                    xbmc.sleep(commDelay)
                    percent = percent + percent_inc
                except Exception as e:
                    errorTrace("trakt.py", "Problem updating " + name + " with new Trakt tokens")
                    errorTrace("trakt.py", str(e))
                    trakt_file.close()
                    if xbmcvfs.exists(trakt_path_old):
                        if xbmcvfs.exists(trakt_path): xbmcvfs.delete(trakt_path)
                        xbmcvfs.rename(trakt_path + ".old", trakt_path)
                        infoTrace("trakt.py", "Replaced " + name + " with original file before modification.")
                    else:
                        infoTrace("trakt.py", "No modifications were done to the original file")
                i += 1

            if updated > 0:
                progDiag.update(100, "Finished modifying Trakt tokens", " ")
                xbmc.sleep(1000)
                progDiag.close()
                if dialogs: xbmcgui.Dialog().ok(addon_name, "Trakt tokens have been modified. Now re-authorize to Trakt in " + list + ". Set up a trigger to update Trakt again if any of the add-ons are updated.")
            else:
                progDiag.update(100, "No Trakt tokens were altered", " ")
                xbmc.sleep(3000)  
                progDiag.close()
                
        
def revertTrakt():
    addon = xbmcaddon.Addon("service.zomboided.tools")
    addon_name = addon.getAddonInfo("name")
#
#    addons, files = getAddons()
#    
#    if len(addons) > 0 and xbmcgui.Dialog().yesno(addon_name, "Revert modified add-ons back to original versions?"):
#        for name in addons:
#            trakt_path = files[i]
#            trakt_path_old = trakt_path + ".old"
#            try:                    
#               progDiag.update(percent, "Reverting " + name + " back to original version.","Please wait.")
#                updated += 1
#                if xbmcvfs.exists(trakt_path_old):
#                    try:
#                        if xbmcvfs.exists(trakt_path): xbmcvfs.delete(trakt_path)
#                        xbmcvfs.rename(trakt_path + ".old", trakt_path)
#                    except Exception as e:
#                        errorTrace("trakt.py", "Problem reverting " + name + " to original version.")
#                        errorTrace("trakt.py", str(e))
#    return