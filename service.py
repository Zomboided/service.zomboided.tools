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
#    Service module for Zomboided Tools addon

import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
import os
import time
import datetime
import urllib2
import re
import string
from libs.utility import setDebug, debugTrace, errorTrace, infoTrace, newPrint

#setDebug(True)

debugTrace("-- Entered service.py --")

# Set the addon name for use in the dialogs
addon = xbmcaddon.Addon()
addon_name = addon.getAddonInfo('name')

update_service = True

# Playlist check variables
playlist_detection_delay = 10
playlist_time_check = True
playlist_max_minutes = 10
playlist_count_check = True
playlist_max_count = 5
playlist_min_count = 1

# Monitor class which will get called when the settings change    
class KodiMonitor(xbmc.Monitor):

    # This gets called every time a setting is changed either programmatically or via the settings dialog.
    def onSettingsChanged( self ):
        debugTrace("Requested update to service process via settings monitor")
        updateSettings()

        
def updateSettings():
    global playlist_detection_delay
    global playlist_time_check
    global playlist_max_minutes
    global playlist_count_check
    global playlist_max_count
    global playlist_min_count
    
    addon = xbmcaddon.Addon()
    
    # Refresh the playlist settings
    if addon.getSetting("stop_playback_time") == "true": playlist_time_check = True
    else: playlist_time_check = False
    playlist_max_minutes = int(addon.getSetting("stop_playback_mins"))
    if addon.getSetting("stop_playback_videos") == "true": playlist_count_check = True
    else: playlist_count_check = False
    playlist_max_count = int(addon.getSetting("stop_playback_count"))
    playlist_min_count = int(addon.getSetting("detect_playlist_minimum"))
    playlist_detection_delay = int(addon.getSetting("detect_playlist_gap"))

    
# Player class which will be called when the playback state changes           
class KodiPlayer(xbmc.Player):
    
    playback_playing = False
    playback_max = 0
    playback_count = 0
    playback_ended = 0

    def __init__ (self):
        xbmc.Player.__init__(self)
        self.logger = None

    def onPlayBackStarted(self, *arg):
        t = now()
        
        # If playback ended some time ago, this isn't a playlist
        if self.playback_playing and t - self.playback_ended > playlist_detection_delay:
            debugTrace("Playlist is over")
            self.resetPlaybackCounts()
        
        if not self.playback_playing:
            # If a playlist isn't active, this is the first video in a playlist (or otherwise)
            updateSettings()
            self.playback_playing = True
            self.playback_max = t + (playlist_max_minutes * 60)
            self.playback_count = 0
            debugTrace("Detected playback starting")
            debugTrace("Max playback time is " + str(playlist_max_minutes))
            debugTrace("Max playback videos is " + str(playlist_max_count))
            debugTrace("Time is " + str(t) + " max time is " + str(self.playback_max))
        else:
            # This is not the first video in a playlist
            if playlist_count_check: debugTrace("Count is " + str(self.playback_count) + ", max is " + str(playlist_max_count) + ", min is " + str(playlist_min_count))
            if playlist_time_check: debugTrace("Time is " + str(t) + ", timeout is " + str(self.playback_max))
            if playlist_count_check and self.playback_count >= playlist_max_count:
                xbmc.Player().stop()
                infoTrace("service.py", "Stopping playlist after playing " + str(playlist_max_count) + " videos.")
                self.resetPlaybackCounts()
            elif playlist_time_check and t > self.playback_max and self.playback_count >= playlist_min_count:
                xbmc.Player().stop()
                infoTrace("service.py", "Stopping playlist after reaching maximum time period")
                self.resetPlaybackCounts()  
        
    def onPlayBackStopped(self, *arg):
        self.resetPlaybackCounts()
        
    def onPlayBackEnded(self, *arg):
        t = now()
        self.playback_ended = t
        self.playback_count += 1

    def resetPlaybackCounts(self):
        self.playback_playing = False
        self.playback_max = 0
        self.playback_count = 0
        self.playback_ended = 0

        
# Return seconds since epoch    
def now():
    return int(time.time())
    
        
if __name__ == '__main__':   

    infoTrace("service.py", "Starting Zomboided Tools service, version is " + addon.getAddonInfo("version"))
    debugTrace("Kodi build is " + xbmc.getInfoLabel('System.BuildVersion'))
    
    updateSettings()
    
    # Initialise some variables we'll be using repeatedly
    monitor = xbmc.Monitor()
    # player = xbmc.Player() 
    addon = xbmcaddon.Addon()
    
    # Monitor to check for settings changes
    settingsMonitor = KodiMonitor()
    # Monitor to limit playback time/number of files
    playerMonitor = KodiPlayer()
    
    # Initialise a bunch of variables
    #timer = 0
    delay = 10
    
    while not monitor.abortRequested():
                  
        # Take multiple naps, checking to see if there are any outstanding CLI commands
        if monitor.waitForAbort(delay):
            # Abort was requested while waiting. We should exit
            infoTrace("service.py", "Abort received, shutting down service")
            break
        
        #timer = timer + delay
