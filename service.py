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
import xbmcvfs
import os
import time
import datetime
import calendar
from libs.utility import setDebug, debugTrace, errorTrace, infoTrace, newPrint, now
from libs.rules import rules, VIDEO_GROUP, EMBY_GROUP, WILDCARD
from libs.trakt import updateTrakt, revertTrakt
from libs.vpnapi import VPNAPI
from libs.common import fixKeymaps, getSleep, setSleep, getSleepReq, setSleepReq, setSleepReqTime, clearSleep, setSleepRemaining, getSleepRemaining
from libs.common import getSleepReqTime, SLEEP_OFF, SLEEP_END, SLEEP_DELAY_TIME, clearAlert, addAlert, activeAlert, forceSleepLock, freeSleepLock


setDebug(False)

# This is here to avoid a known Python locking bug https://bugs.python.org/issue7980
for i in range(1, 10):
    try:
        datetime.datetime(*(time.strptime('2018-01-01', '%Y-%m-%d')[0:6]))
        break
    except Exception as e:
        errorTrace("service.py", "Couldn't call strptime cleanly during initialisation, call" + str(i))
        errorTrace("service.py", str(e))
        xbmc.sleep(3000)
      
debugTrace("-- Entered service.py --")

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Number of actions enabled in the settings screen
ACTION_COUNT = 10

# Like an action, but in the land of nod
SLEEP_ACTION = "Zzzz"

# Used in parse timer
TODAY = -1
TOMORROW = 0

# Set the addon name for use in the dialogs
addon = xbmcaddon.Addon()
addon_name = addon.getAddonInfo('name')

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
addon_check_freq = 0
file_check_freq = 0
refresh_check_freq = 0

# Timers
sleep_timer = 0
action_timer = 0
action_timer_number = 0
addon_timer = 0
addon_timer_start = 0
addon_timer_end = 0
last_boot = 0
playback_timer = 0
file_timer = 0
file_timer_start = 0
file_timer_end = 0
refresh_timer = 0
auto_sleep_start = 0
auto_sleep_end = 0


# Monitor class which will get called when the settings change    
class KodiMonitor(xbmc.Monitor):

    # This gets called every time a setting is changed either programmatically or via the settings dialog.
    def onSettingsChanged( self ):
        #debugTrace("Requested update to service process via settings monitor")
        updateSettings("onSettingsChanged", False)


# Pick through the addon settings and translate them to variables we'll be using        
def updateSettings(caller, wait):
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
    global addon_timer
    global addon_timer_start
    global addon_timer_end
    global addon_check_freq
    global file_timer
    global file_timer_start
    global file_timer_end
    global file_check_freq
    global refresh_timer
    global refresh_check_freq
    global auto_sleep_start
    global auto_sleep_end
    
    if not updatesAllowed() and not wait: return
    
    # Wait for 60 seconds, then carry on anyway
    for i in range(1, 60):
        if updatesAllowed(): break
        xbmc.sleep(1000)
        if i == 59: errorTrace("service.py", "updateSettings was called from " + caller + " with wait, but could not get a lock to update after 60 seconds")
    
    debugTrace("updateSettings called from " + caller)
    refresh_timer = 0
    allowUpdates(False)
    
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
    for i in range(1, (ACTION_COUNT + 1)):
        fixWarnTime("action_warn_" + str(i))
    fixWarnTime("sleep_warn")
    addon = xbmcaddon.Addon()
        
    # Refresh the action settings
    action_timer = 0
    action_timer_number = 0
    for i in range(0, ACTION_COUNT):
        # Check the timer settings
        j = str(i+1)
        next_action_timer = parseTimer("Action Timer " + j,
                                       addon.getSetting("action_timer_freq_" + j),
                                       addon.getSetting("action_time_" + j),
                                       addon.getSetting("action_day_" + j),
                                       addon.getSetting("action_date_" + j),
                                       addon.getSetting("action_period_" + j),
                                       0)
        # Determine if this time is the nearest one and use it if it is
        if (action_timer == 0 and not next_action_timer == 0) or (next_action_timer > 0 and next_action_timer < action_timer):
            action_timer_number = i + 1
            action_timer = next_action_timer
            
        if addon.getSetting("action_addon_enabled_" + j) == "true":
            selected = addon.getSetting("action_addon_" + j)
            last = addon.getSetting("addon_name_" + j)
            if not selected == last: addon_timer = addon_check_freq + 1
        
    t = now()
    
    # Frequency add-ons are checked
    addon_check_freq = int(addon.getSetting("addon_check"))*60
    addon_timer_start, addon_timer_end = parseTimePeriod(t, "Addon Check", addon.getSetting("addon_check_start"), addon.getSetting("addon_check_end"))
    
    # Frequency files are checked
    file_check_freq = int(addon.getSetting("file_check"))*60
    file_timer_start, file_timer_end = parseTimePeriod(t, "File Check", addon.getSetting("file_check_start"), addon.getSetting("file_check_end"))

    # Auto sleep timers
    auto_sleep_start, auto_sleep_end = parseTimePeriod(t, "Auto Sleep", addon.getSetting("auto_sleep_start"), addon.getSetting("auto_sleep_end"))

    # Settings get refreshed infrequently, just in case...
    refresh_check_freq = int(addon.getSetting("refresh_check"))*60
    
    if not action_timer_number == 0:
        debugTrace("Action timer " + str(action_timer_number) + " is the first timer with " + str(action_timer))
    else:
        debugTrace("No action timers are set")
    allowUpdates(True)

    
def allowUpdates(bool):
    xbmc.sleep(1000)
    if bool:
        xbmcgui.Window(10000).setProperty("Zomboided_Tools_Settings_Updates", "True")
    else: 
        xbmcgui.Window(10000).setProperty("Zomboided_Tools_Settings_Updates", "False")
    xbmc.sleep(1000)
    return 
    
    
def updatesAllowed():
    if xbmcgui.Window(10000).getProperty("Zomboided_Tools_Settings_Updates") == "False": return False
    return True

    
# Fix the warning timer settings if necessary                             
def fixWarnTime(warning):
    w = int(addon.getSetting(warning))
    if w > 0:
        if w > 10: new_w = int(w / 10) * 10
        else: new_w = 10
        if not w == new_w: addon.setSetting(warning, str(new_w))                           
                             
                             
def parseTimer(type, freq, rtime, day, date, period, begin):
    debugTrace("Parsing " + type + ". Frequency is " + freq + ", time is + " + rtime + ", day is " + day + ", date is " + date + ", period is " + period)
    if freq == "" or freq == "Off": 
        return 0
    else:
        # Assume timer is today at the defined reboot time
        timer = time.strftime("%d %m %Y") + " " + rtime
        # Parse the timer starting from a given time, or now
        if begin > 0:
            t = begin
        else:
            t = now()
        # Make some datetime objects representing now, last boot time and the timer
        current_dt = datetime.datetime.fromtimestamp(t)
        last_dt = datetime.datetime.fromtimestamp(last_boot)
        #xbmc.sleep(1000)
        #try:
        #    timer_dt = datetime.datetime.strptime(timer, "%d %m %Y %H:%M")
        #except:
        timer_dt = datetime.datetime(*(time.strptime(timer, "%d %m %Y %H:%M")[0:6]))
        # Adjust timer based on the frequency
        if freq == "Daily":
            # If the timer is in the past, add a day
            if timer_dt < current_dt and not begin == TODAY: 
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
        debugTrace("Starting time is " + str(current_dt) + ", last reboot is " + str(last_dt) + ", timer is " + str(timer_dt))
        diff_seconds = int((timer_dt - current_dt).total_seconds())
        return (t + diff_seconds)

        
def parseTimePeriod(t, timer_name, start_time, end_time):
    happy = False
    start = TODAY
    while not happy:
        timer_start = parseTimer(timer_name + " Start", "Daily", start_time, "", "", "", start)
        timer_end = parseTimer(timer_name + " End", "Daily", end_time, "", "", "", timer_start)
        # If the scheduled time is in the past, try again for the next day
        if timer_end < t: start = TOMORROW
        else: happy = True
    return timer_start, timer_end
    

# Player class which will be called when the playback state changes           
class KodiPlayer(xbmc.Player):
    
    playlist_playing = False
    playlist_max = 0
    playlist_count = 0
    playlist_ended = 0
    playing_file = False

    def __init__ (self):
        xbmc.Player.__init__(self)
        self.logger = None

    def onPlayBackStarted(self, *arg):
        global playback_timer
        
        addon = xbmcaddon.Addon()
        
        # Deal with endPlayback not being called previously
        if self.playing_file: self.runPlaybackEnded()
        self.playing_file = True
        
        t = now()
        
        # Determine the end time if there's a play back limit
        d_timer = 0
        t_timer = 0
        playback_timer = 0
        
        if playback_duration_check: d_timer = t + (playback_duration_minutes * 60)
        if playback_time_check: t_timer = parseTimer("Play back timer", "Daily", playback_time, "", "", "", 0)
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
            updateSettings("onPlayBackStarted", True)
            self.playlist_playing = True
            self.playlist_max = t + (playlist_max_minutes * 60)
            self.playlist_count = 1
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
        
        if addon.getSetting("auto_sleep") == "true" and t > auto_sleep_start and t < auto_sleep_end:
            if getSleep() == "Off":
                setSleepReq("End")
                setSleepReqTime(t-SLEEP_DELAY_TIME)
                xbmcgui.Dialog().notification("Sleeping at end of video." , "", "", 2000, False)
                addAlert()
        
        
    def onPlayBackStopped(self, *arg):
        global playback_timer
        global sleep_timer
        self.playing_file = False
        playback_timer = 0
        self.resetPlaybackCounts()
        debugTrace("Playback stopped, sleep is " + getSleep())
        if getSleep() == "End":
            addAlert()
            sleep_timer = 1
        
    def onPlayBackEnded(self, *arg):
        self.runPlaybackEnded("onPlayBackEnded")

    def resetPlaybackCounts(self):
        self.playlist_playing = False
        self.playlist_max = 0
        self.playlist_count = 0
        self.playlist_ended = 0

    def runPlaybackEnded(self, caller):
        global playback_timer
        global sleep_timer
        self.playing_file = False
        playback_timer = 0
        t = now()
        self.playlist_ended = t
        self.playlist_count += 1
        debugTrace("Playback ended called from " + caller + ", at " + str(self.playlist_ended) + ", count is " + str(self.playlist_count) + " sleep is " + getSleep())
        if getSleep() == "End":
            addAlert()
            sleep_timer = 1
        
    def isStillPlaying(self):
        return self.playing_file
        
        
if __name__ == '__main__':   

    infoTrace("service.py", "Starting Zomboided Tools service, version is " + addon.getAddonInfo("version"))
    infoTrace("service.py", "Kodi build is " + xbmc.getInfoLabel('System.BuildVersion'))

    monitor = KodiMonitor()
    player = KodiPlayer()

    api = None
    if xbmc.getCondVisibility("System.HasAddon(service.vpn.manager)"):
        try:
            api = VPNAPI()
        except Exception as e:
            errorTrace("service.py", "Couldn't connect to the VPN Mgr API")
            errorTrace("service.py", str(e))
            api = None
    
    # Initialise some variables we'll be using repeatedly    
    addon = xbmcaddon.Addon()
    
    allowUpdates(False)
    addon.setSetting("boot_time", time.strftime('%Y-%m-%d %H:%M:%S'))
    allowUpdates(True)
    
    last_boot = now()
    
    updateSettings("main initialisation", True)
    
    # Initialise a bunch of variables
    delay = 10
    delay_loop = 6

    file_timer = 0
    action_number_f = 0
    addon_timer = 0
    action_number_a = 0
    last_sleep = SLEEP_OFF
    sleep_timer = 0
    sleep_notify = 0
    notify_mins = "0"
    clearSleep()

    do_it = False    
    action_if_playing = False
    action = ""
    warn = -1
    action_number = 0
          
    # Load the rules
    rules = rules(True)
    rules.preloadRulesAddons()
              
    # Check the keymaps for this add-on are intact
    if fixKeymaps():
        xbmcgui.Dialog().ok(addon_name, "The keymap had been renamed.  This has been reverted to the correct name, but you must restart for the keymap to take effect.") 
              
    while not monitor.abortRequested():
    
        t = now()

        # This copes with endPlayback not being called properly (for whatever reason)
        if player.isStillPlaying() and not player.isPlaying():
            player.runPlaybackEnded("main loop")
        
        if playback_timer > 0 and t > playback_timer:
            player.stop()
            infoTrace("service.py", "Stopping play back.  Duration is " + str(playback_duration_minutes) + " minutes, time limit is " + str(playback_time))
           
        # Sleep Checking
        if sleep_timer > 0 and not do_it:
            if t >= sleep_timer:
                sleep_timer = 0
                do_it = True
                action_number = SLEEP_ACTION
                action = addon.getSetting("sleep_action")
                warn = int(addon.getSetting("sleep_warn"))
                action_if_playing = True
                infoTrace("service.py", "Sleep timer has triggered on " + str(t) + ".")
                last_sleep = SLEEP_OFF
                setSleep(SLEEP_OFF)
            if sleep_notify > 0 and t > sleep_notify:
                sleep_notify = 0
                xbmcgui.Dialog().notification("Sleeping in " + notify_mins + " minutes." , "", "", 3000, False)
        
        # Timer Checking
        if action_timer > 0 and t >= action_timer and not do_it:
            do_it = True
            action_number = str(action_timer_number)
            action = addon.getSetting("action_" + action_number)
            warn = int(addon.getSetting("action_warn_" + action_number))
            action_if_playing = False
            if addon.getSetting("action_if_playing_" + action_number) == "true": action_if_playing = True
            infoTrace("service.py", "Timer " + str(action_timer) + " has triggered on " + str(t) + " for action #" + action_number + ".")
            
        # File Checking
        if not player.isPlaying() and file_timer >= file_check_freq and not do_it:
            allowUpdates(False)
            action_number_f += 1
            if action_number_f > ACTION_COUNT:
                action_number_f = 1
            action_number = str(action_number_f)
            debugTrace("Checking file for action #" + action_number)
            if addon.getSetting("action_file_enabled_" + action_number) == "true":
                unavailable = False
                if addon.getSetting("action_file_unavailable_" + action_number) == "true": unavailable = True
                file = addon.getSetting("action_file_" + action_number)
                last_file_time = addon.getSetting("file_time_" + action_number)
                last_reboot = addon.getSetting("file_reboot_" + action_number)
                file_error = False
                if not file == "":
                    if xbmcvfs.exists(file):
                        try:
                            stats = xbmcvfs.Stat(file)
                            file_time = str(stats.st_mtime())
                            addon.setSetting("file_reboot_" + action_number, "")
                            debugTrace("Checking file " + file + " " + file_time + " with " + last_file_time)
                            if last_file_time == "":
                                addon.setSetting("file_time_" + action_number, file_time)
                            elif not last_file_time == file_time:
                                addon.setSetting("file_time_" + action_number, file_time)
                                do_it = True
                                infoTrace("service.py", "File " + file + " had time stamp " + last_file_time + " and now has " + file_time + ", triggering action #" + action_number + ".")
                        except Exception as e:                        
                            errorTrace("service.py", "Couldn't get the time stamp of " + file + " for action #" + action_number + ", will try again later.")
                            errorTrace("service.py", str(e))
                            file_error = True
                    else:
                        infoTrace("service.py", "File " + file + " does not exist for action #" + action_number + ", will try again later.")
                        file_error = True
                    # Take action if file unavailable after 2 tries, and never take the action more than once (avoid reboot loops, etc)
                    if file_error and unavailable:
                        if last_reboot == "" : 
                            addon.setSetting("file_reboot_" + action_number, "pending")
                        else :
                            do_it = True
                            addon.setSetting("file_reboot_" + action_number, "true")
                            infoTrace("service.py", "File " + file + " still cannot be found or accessed and is triggering action #" + action_number + ".")
                else:
                    if not last_file_time == "":
                        addon.setSetting("file_time_" + action_number, "")
                    if not last_reboot == "":
                        addon.setSetting("file_reboot_" + action_number, "")
                addon = xbmcaddon.Addon()
                if do_it:
                    action = addon.getSetting("action_" + action_number)
                    warn = int(addon.getSetting("action_warn_" + action_number))
                    action_if_playing = True
            if action_number_f == ACTION_COUNT: file_timer = 0
            allowUpdates(True)
            
        # Add-on Checking
        if not player.isPlaying() and addon_timer >= addon_check_freq and not do_it:            
            allowUpdates(False)
            action_number_a += 1
            if action_number_a > ACTION_COUNT:
                action_number_a = 1
            action_number = str(action_number_a)
            debugTrace("Checking add-on for action # " + action_number)
            if addon.getSetting("action_addon_enabled_" + action_number) == "true":
                # Get the current list of add-ons and previously detected settings
                addons_s = addon.getSetting("action_addon_" + action_number)
                addons_l = addons_s.split(",")
                last_s = addon.getSetting("addon_name_" + action_number)
                last_l = last_s.split(",")
                versions_s = addon.getSetting("addon_version_" + action_number)
                versions_l = versions_s.split(",")
                debugTrace("Addons are " + addons_s + ", previous addons are " + last_s + ", versions are " + versions_s)
                # Compare the previous with the versions now
                if len(addons_l) > 0 and addons_s == last_s:
                    if len(versions_l) == len(last_l):
                        i = 0
                        for i in range(0, len(last_l)):
                            try:
                                command = "System.HasAddon(" + last_l[i] + ")"
                                if xbmc.getCondVisibility(command):
                                    version = xbmcaddon.Addon(last_l[i]).getAddonInfo("version")
                                else:
                                    version = " "
                            except Exception as e:
                                version = " "
                            if version == " ":
                                if not versions_l[i] == version :
                                    errorTrace("service.py", "Add-on " + last_l[i] + ", is not available to check as part of action #" + action_number)
                                    last_s = ""
                                else:
                                    debugTrace("Add-on " + last_l[i] + ", is still not available to check as part of action #" + action_number)
                            elif not version == versions_l[i]:
                                infoTrace("service.py", "Add-on " + last_l[i] + ", has been updated from " + versions_l[i] + " to " + version)
                                do_it = True
                                action = addon.getSetting("action_" + action_number)
                                warn = int(addon.getSetting("action_warn_" + action_number))
                                action_if_playing = True
                                # Force new list of versions to be build below
                                last_s = ""
                                break
                    else:
                        last_s = ""
                    
                if last_s == "" or not addons_s == last_s:
                    # Addons list is different, reset to current versions
                    addon.setSetting("addon_name_" + action_number, addons_s)
                    versions = ""
                    for name in addons_l:
                        try:
                            command = "System.HasAddon(" + name + ")"
                            if xbmc.getCondVisibility(command):
                                version = xbmcaddon.Addon(name).getAddonInfo("version")
                            else:
                                version = " "
                        except:
                            version = " "
                        if versions == "": versions = version
                        else: versions = versions + "," + version
                    addon.setSetting("addon_version_" + action_number, versions)
            else:
                if not addon.getSetting("addon_name_" + action_number) == "":
                    addon.setSetting("addon_name_" + action_number, "")
                    addon.setSetting("addon_version_" + action_number, "")
            if action_number_a == ACTION_COUNT: addon_timer = 0
            allowUpdates(True)
            addon = xbmcaddon.Addon()
        
        # Set up sleep timer
        sleep_setting = getSleepReq()
        if not sleep_setting == "":
            if t - getSleepReqTime() < SLEEP_DELAY_TIME:
                # This reduces the loop time so that sleep changes are noticed in a reasonable time
                addAlert()
            else:
                forceSleepLock()
                infoTrace("service.py", "Setting a sleep timer, " + sleep_setting + ". Previous was " + last_sleep)
                last_sleep = sleep_setting
                if sleep_setting == SLEEP_OFF or sleep_setting == SLEEP_END:
                    sleep_timer = 0
                    sleep_notification = 0
                    setSleepRemaining("")
                else:
                    if sleep_setting.isdigit():
                        sleep_timer = t + (int(sleep_setting) * 60)
                        notify_mins = addon.getSetting("sleep_notify")
                        sleep_notify = 0
                        if not (notify_mins == "" or notify_mins == "0"):
                            sleep_notify = sleep_timer - (int(notify_mins) * 60)
                        debugTrace("Time now is " + str(t) + ", sleep timer set for " + str(sleep_timer) + ", sleep notify is " + str(sleep_notify))
                    else:
                        errorTrace("Sleep timer was bad, found" + sleep_setting)
                        sleep_timer = 0
                        setSleepRemaining("")
                        sleep_setting = SLEEP_OFF
                setSleep(sleep_setting)
                setSleepReq("")
                freeSleepLock()
        
        # Update sleep remaining for sleep cycle display elsewhere
        sleep_setting = getSleep()
        if not (sleep_setting == SLEEP_OFF or sleep_setting == SLEEP_END):
            setSleepRemaining(str((sleep_timer - t)/60))
        
        # Take any outstanding action
        if do_it and (not player.isPlaying() or (player.isPlaying() and action_if_playing)):
            if action == "Stop Playing" and not player.isPlaying():
                if not action_number == SLEEP_ACTION or (action_number == SLEEP_ACTION and not addon.getSetting("sleep_cec_off") == "true"):
                    # There's nothing to do here...
                    do_it = False
                    infoTrace("service.py", action + " unnecessary")
            if do_it and warn > 0 and not action == "None":
                msg = ""
                if action_number == SLEEP_ACTION: 
                    msg = "Going to sleep. "
                if not action == "Stop Playing" or (action == "Stop Playing" and player.isPlaying()):
                    msg = msg + "About to " + action + ". "
                msg = msg + "Click cancel to abort. "
                if action == "Clear Cache":
                    msg = msg + "[COLOR red][B]Avoid using any input device until cache clearance is complete.[/B][/COLOR]"
                if action == "Run Command":
                    if action_number == SLEEP_ACTION: c = addon.getSetting("sleep_command")
                    else: c = addon.getSetting("action_command_" + action_number)
                    msg = msg + "Command is '[I]" + c + "'[/I]" 
                dialog = xbmcgui.DialogProgress()
                dialog.create(addon_name, msg)
                dialog.update(100)
                xbmc.sleep(1000)
                tick = int(100 / warn)
                for i in range(1, 100):
                    if dialog.iscanceled():
                        do_it = False
                        infoTrace("service.py", action + " aborted by user")
                        break
                    percent = 100-(i*tick)
                    if percent < 0: break
                    dialog.update(percent)
                    xbmc.sleep(1000)
                dialog.close()
            if do_it:
                infoTrace("service.py", "Trigger fired for action #" + action_number + ", performing a " + action)
                if action_number == SLEEP_ACTION and addon.getSetting("sleep_cec_off") == "true":
                    infoTrace("service.py", "Turning off TV before action " + action)
                    xbmc.executebuiltin("CECStandby")
                if action == "None":
                    xbmcgui.Dialog().ok(addon_name, "Trigger has fired for action #" + action_number + ", but no action is defined.")
                elif action == "Stop Playing":
                    player.stop()
                elif action == "Reset video add-ons":
                    mask = addon.getSetting("video_mask")
                    if mask == WILDCARD: mask = ""
                    rules.runRules(False, VIDEO_GROUP, mask)
                elif action == "Modify Trakt add-ons":
                    updateTrakt(10000, False)
                    if addon.getSetting("trakt_clear") == "true":
                        rules.runRules(False, "Video", mask)
                elif action == "Reset Emby":
                    mask = addon.getSetting("emby_mask")
                    if mask == WILDCARD: mask = ""
                    rules.runRules(False, EMBY_GROUP, mask)
                elif action == "Disconnect VPN":
                    if api is not None:
                        result = api.disconnect(False)
                    else:
                        xbmcgui.Dialog().ok(addon_name, "Trigger has fired for action #" + action_number + ", but VPN Manager is not available.")
                elif action == "Reconnect VPN":
                    if api is not None:
                        result = api.reconnect(True)
                    else:
                        xbmcgui.Dialog().ok(addon_name, "Trigger has fired for action #" + action_number + ", but VPN Manager is not available.")
                elif action == "Run Command":
                    if action_number == SLEEP_ACTION: c = addon.getSetting("sleep_command")
                    else: c = addon.getSetting("action_command_" + action_number)
                    infoTrace("service.py", "Executing command '" + c + "'")
                    try:
                        xbmc.executebuiltin(c)
                    except Exception as e:
                        xbmcgui.Dialog().ok(addon_name, "Trigger has fired for action #" + action_number + ", but command failed to run.  See log for details.")
                        errorTrace("service.py", "Could not run command '" + c + "' for action #" + action_number + ". Error shown on next line.")
                        errorTrace("service.py", str(e))
                elif action == "Run custom rules":
                    group = addon.getSetting("action_rules_group_" + action_number)
                    mask = addon.getSetting("action_rules_mask_" + action_number)
                    if mask == WILDCARD: mask = ""
                    rules.runRules(False, group, mask)
                else:
                    xbmc.executebuiltin(action)
                
            # Get the next timer setting
            updateSettings("main after action", True)
            
            do_it = False
            action_if_playing = False
        
        # If the settings haven't been updated in a while, force one anyway because of timing windows
        if not player.isPlaying() and refresh_timer >= refresh_check_freq:
            # FIXME remove these debug statements
            debugTrace("Time now is " + str(t) + ", " + str(datetime.datetime.fromtimestamp(t)) + ", next action timer is " + str(datetime.datetime.fromtimestamp(action_timer)))
            debugTrace("Addon timer is " + str(addon_timer) + "/" + str(addon_check_freq) + ", file timer is " + str(file_timer) + "/" + str(file_check_freq))
            updateSettings("main refresh timer", True)
        
        # Have a nap before checking timers again
        delay_count = 0
        for i in range(0, delay_loop):
            delay_count += delay
            if monitor.waitForAbort(delay):
                # Abort was requested while waiting. We should exit
                infoTrace("service.py", "Abort received, shutting down service")
                break
            if activeAlert() or not player.isPlaying(): break
                      
        clearAlert()
        # FIXME could do something clever here to trigger on transition between not counting and starting to count so that
        # another hour or so isn't added on to the checking start time.  Not sure if this works if it's on all the time?
        if t > addon_timer_start and t < addon_timer_end : addon_timer = addon_timer + delay_count
        if t > file_timer_start and t < file_timer_end : file_timer = file_timer + delay_count
        refresh_timer = refresh_timer + delay_count