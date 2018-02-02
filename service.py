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
#    Service module for Zomboided Tools add-on

import xbmc
import xbmcgui
import xbmcaddon
import os
import time
import datetime
import calendar
from libs.utility import setDebug, debugTrace, errorTrace, infoTrace, newPrint, now
from libs.cache import clearCache

setDebug(True)

# This is here to avoid a known Python locking bug https://bugs.python.org/issue7980
datetime.datetime.strptime('2018-01-01', '%Y-%m-%d')

debugTrace("-- Entered service.py --")

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Number of timers enabled in the settings screen
TIMER_COUNT = 5

# Set the addon name for use in the dialogs
addon = xbmcaddon.Addon()
addon_name = addon.getAddonInfo('name')

allow_updates = False

# Playlist check variables
playback_duration_check = False
playback_duration_minutes = 0
playback_time_check = False
playback_time = 0
playlist_detection_delay = 0
playlist_time_check = False
playlist_max_minutes = 0
playlist_count_check = False
playlist_max_count = 0
playlist_min_count = 0

# Timers
action_timer = 0
action_timer_number = 0
last_boot = 0
playback_timer = 0

# Monitor class which will get called when the settings change    
class KodiMonitor(xbmc.Monitor):

    # This gets called every time a setting is changed either programmatically or via the settings dialog.
    def onSettingsChanged( self ):
        debugTrace("Requested update to service process via settings monitor")
        updateSettings()


# Pick through the addon settings and translate them to variables we'll be using        
def updateSettings():
    global playback_duration_check
    global playback_duration_minutes
    global playback_time_check
    global playback_time
    global playlist_detection_delay
    global playlist_time_check
    global playlist_max_minutes
    global playlist_count_check
    global playlist_max_count
    global playlist_min_count
    global action_timer
    global action_timer_number
    global cache_timer
    global allow_updates
    
    if not allow_updates: return
    
    allow_updates = False
    
    addon = xbmcaddon.Addon()
    
    # Refresh the play limit settings
    if addon.getSetting("stop_playback_duration") == "true": playback_duration_check = True
    else: playback_duration_check = False
    playback_duration_minutes = int(addon.getSetting("stop_playback_mins"))
    if addon.getSetting("stop_playback_after") == "true": playback_time_check = True
    else: playback_time_check = False
    playback_time = addon.getSetting("stop_playback_time")
    
    # Refresh the playlist settings
    if addon.getSetting("stop_playlist_time") == "true": playlist_time_check = True
    else: playlist_time_check = False
    playlist_max_minutes = int(addon.getSetting("stop_playlist_mins"))
    if addon.getSetting("stop_playlist_videos") == "true": playlist_count_check = True
    else: playlist_count_check = False
    playlist_max_count = int(addon.getSetting("stop_playlist_count"))
    playlist_min_count = int(addon.getSetting("detect_playlist_minimum"))
    playlist_detection_delay = int(addon.getSetting("detect_playlist_gap"))
    
    # The warning timers should be 10 second increments so fix if it's not
    for i in range(1, (TIMER_COUNT + 1)):
        fixWarnTime("action_warn_" + str(i))
    addon = xbmcaddon.Addon()
        
    # Refresh the reboot timer settings
    action_timer = 0
    action_timer_number = 0
    for i in range(0, TIMER_COUNT):
        j = str(i+1)
        next_action_timer = parseTimer("Action Timer " + j,
                                       addon.getSetting("action_timer_freq_" + j),
                                       addon.getSetting("action_time_" + j),
                                       addon.getSetting("action_day_" + j),
                                       addon.getSetting("action_date_" + j),
                                       addon.getSetting("action_period_" + j))
                                      
        if (action_timer == 0 and not next_action_timer == 0) or (next_action_timer > 0 and next_action_timer < action_timer):
            action_timer_number = i + 1
            action_timer = next_action_timer
           
    # FIXME read in the addons here and get the current version
    
    # FIXME read in the files here
           
    debugTrace("Action timer " + str(action_timer_number) + " is the first timer with " + str(action_timer))
    allow_updates = True                         

    
# Fix the warning timer settings if necessary                             
def fixWarnTime(warning):
    w = int(addon.getSetting(warning))
    if w > 0:
        if w > 10: new_w = int(w / 10) * 10
        else: new_w = 10
        if not w == new_w: addon.setSetting(warning, str(new_w))                           
                             
                             
def parseTimer(type, freq, rtime, day, date, period):
    debugTrace("Parsing " + type + ". Frequency is " + freq + ", time is + " + rtime + ", day is " + day + ", date is " + date + ", period is " + period)
    if freq == "" or freq == "Off": 
        return 0
    else:
        # Assume timer is today at the defined reboot time
        timer = time.strftime("%d %m %Y") + " " + rtime
        # Sleep to avoid some weird thread locking problem
        t = now()
        # Make some datetime objects representing now, last boot time and the timer
        current_dt = datetime.datetime.fromtimestamp(t)
        last_dt = datetime.datetime.fromtimestamp(last_boot)
        timer_dt = datetime.datetime.strptime(timer, "%d %m %Y %H:%M")
        # Adjust timer based on the frequency
        if freq == "Daily":
            # If the timer is in the past, add a day
            if timer_dt < current_dt: 
                d = datetime.timedelta(days = 1)
                timer_dt = timer_dt + d
        elif freq == "Weekly":
            # Calculate the next boot day
            current_day = current_dt.weekday()
            timer_day = days.index(day)
            if current_day > timer_day:
                adjust_day = current_day - timer_day + 1
            elif timer_day < current_day:
                adjust_day = timer_day - current_day
            else:
                # Same day, if it's in the past, add a week
                if timer_dt < current_dt: adjust_day = 7
                else: adjust_day = 0
            # Adjust the timer the required number of days
            if adjust_day > 0:
                d = datetime.timedelta(days = adjust_day)
                timer_dt = timer_dt + d
        elif freq == "Monthly":
            new_day = int(date)
            if (current_dt.day > new_day) or (current_dt.day == new_day and timer_dt < current_dt):
                if current_dt.month == 12:
                    timer_dt = timer_dt.replace(month = 1)
                    timer_dt = timer_dt.replace(year = timer_dt.year + 1)
                else:
                    timer_dt = timer_dt.replace(month = timer_dt.month + 1)
                _, max_day = calendar.monthrange(timer_dt.year, timer_dt.month)
                if new_day > max_day: new_day = max_day 
                timer_dt = timer_dt.replace(day = new_day)
        elif freq == "Periodically":
            timer_dt == datetime.datetime.combine(last_dt.date(), timer_dt.timetz())
            d = datetime.timedelta(days = int(period))
            timer_dt = timer_dt + d
        else:
            errorTrace("service.py", "Couldn't parse timer, no timer set")
            return 0
        # Calculate the difference between the dates and return the timer value in epoch seconds
        debugTrace("Time now is " + str(current_dt) + ", last reboot is " + str(last_dt) + ", timer is " + str(timer_dt))
        diff_seconds = int((timer_dt - current_dt).total_seconds())
        return (t + diff_seconds)

        
# Player class which will be called when the playback state changes           
class KodiPlayer(xbmc.Player):
    
    global playback_timer
    
    playlist_playing = False
    playlist_max = 0
    playlist_count = 0
    playlist_ended = 0

    def __init__ (self):
        xbmc.Player.__init__(self)
        self.logger = None

    def onPlayBackStarted(self, *arg):
        t = now()
        
        # Determine the end time if there's a play back limit
        d_timer = 0
        t_timer = 0
        if playback_duration_check: d_timer = t + (playback_duration_minutes * 60)
        if playback_time_check: t_timer = parseTimer("Play back timer", "Daily", playback_time, "", "", "")
        if not d_timer == 0 and (d_timer < t_timer or t_timer == 0): playback_timer = d_timer
        if not t_timer == 0 and (t_timer < d_timer or d_timer == 0): playback_timer = t_timer
        if playback_timer: debugTrace("Time is " + str(t) + " playing until " + str(playback_timer) + ". Duration was " + str(playback_duration_minutes) + ", time was " + playback_time)
        
        # If playback ended some time ago, this isn't a playlist
        if self.playlist_playing and t - self.playlist_ended > playlist_detection_delay:
            debugTrace("Playlist is over")
            debugTrace("Ended because time between videos was " + str(t-self.playlist_ended) + " seconds, max is " + str(playlist_detection_delay))
            self.resetPlaybackCounts()
        
        if not self.playlist_playing:
            # If a playlist isn't active, this is the first video in a playlist (or otherwise)
            updateSettings()
            self.playlist_playing = True
            self.playlist_max = t + (playlist_max_minutes * 60)
            self.playlist_count = 0
            debugTrace("Detected playback starting")
            debugTrace("Max playback time is " + str(playlist_max_minutes))
            debugTrace("Max playback videos is " + str(playlist_max_count))
            debugTrace("Time is " + str(t) + " max time is " + str(self.playlist_max))
        else:
            # This is not the first video in a playlist
            if playlist_count_check: debugTrace("Count is " + str(self.playlist_count) + ", max is " + str(playlist_max_count) + ", min is " + str(playlist_min_count))
            if playlist_time_check: debugTrace("Time is " + str(t) + ", timeout is " + str(self.playlist_max))
            if playlist_count_check and self.playlist_count >= playlist_max_count:
                xbmc.Player().stop()
                infoTrace("service.py", "Stopping playlist after playing " + str(playlist_max_count) + " videos.")
                self.resetPlaybackCounts()
            elif playlist_time_check and t > self.playlist_max and self.playlist_count >= playlist_min_count:
                xbmc.Player().stop()
                infoTrace("service.py", "Stopping playlist after reaching maximum time period")
                self.resetPlaybackCounts()  
        
    def onPlayBackStopped(self, *arg):
        self.resetPlaybackCounts()
        
    def onPlayBackEnded(self, *arg):
        t = now()
        self.playlist_ended = t
        self.playlist_count += 1
        playback_timer = 0

    def resetPlaybackCounts(self):
        playback_timer = 0
        self.playlist_playing = False
        self.playlist_max = 0
        self.playlist_count = 0
        self.playlist_ended = 0

        
if __name__ == '__main__':   

    infoTrace("service.py", "Starting Zomboided Tools service, version is " + addon.getAddonInfo("version"))
    debugTrace("Kodi build is " + xbmc.getInfoLabel('System.BuildVersion'))

    # Set up the general monitor class
    monitor = KodiMonitor()
    # Set up a player monitor class
    playerMonitor = KodiPlayer()

    # Initialise some variables we'll be using repeatedly    
    addon = xbmcaddon.Addon()
    addon.setSetting("boot_time", "Boot time : " + time.strftime('%Y-%m-%d %H:%M:%S'))
    last_boot = now()
    
    allow_updates = True
    updateSettings()
    
    # Initialise a bunch of variables
    delay = 60
    
    while not monitor.abortRequested():
    
        t = now()

        if playback_timer > 0 and t > playback_timer:
            xbmc.Player().stop()
            infoTrace("service.py", "Stopping play back.  Duration is " + str(playback_duration_minutes) + " minutes, time limit is " + str(playback_time))
            
        if action_timer > 0 and t > action_timer:
            action = addon.getSetting("action_" + str(action_timer_number))
            warn = int(addon.getSetting("action_warn_" + str(action_timer_number)))
            do_it = True
            if warn > 0:
                msg = "About to " + action + ", click cancel to abort."
                if action == "Clear Cache":
                    msg = msg + "\n[COLOR red][B]Avoid using any input device until cache clearance is complete.[/B][/COLOR]"
                dialog = xbmcgui.DialogProgress()
                dialog.create(addon_name, msg)
                dialog.update(100)
                xbmc.sleep(1000)
                tick = int(100 / warn)
                for i in range(1, 100):
                    if dialog.iscanceled():
                        do_it = False
                        break
                    percent = 100-(i*tick)
                    if percent < 0: break
                    dialog.update(percent)
                    xbmc.sleep(1000)
                dialog.close()
            if do_it:
                infoTrace("service.py", "Trigger fired, performing a " + action)
                if action == "Clear Cache":
                    clearCache(10000)
                elif action == "Run Command":
                    # FIXME
                    a = 1
                else:
                    infoTrace("service.py", "Trigger fired, performing a " + action)
                    xbmc.executebuiltin(action)
            else:
                infoTrace("service.py", action + " aborted by user")
                
            # Get the next timer setting
            updateSettings()
        
        # FIXME
        # if not playing, check the versions and the files

        
        # Take a nap before checking timers again
        if monitor.waitForAbort(delay):
            # Abort was requested while waiting. We should exit
            infoTrace("service.py", "Abort received, shutting down service")
            break
