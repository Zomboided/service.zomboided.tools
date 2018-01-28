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
#    This module sets up the sleep timer, allowing the user to configure
#    a button on a remote, etc to call it

import xbmcgui
import xbmcaddon
from libs.utility import debugTrace, errorTrace, infoTrace, newPrint, now
from libs.sleepbox import showSleepBox


def requestSleepCycle():
    addon = xbmcaddon.Addon("service.zomboided.tools")
    sleep_inc = int(addon.getSetting("sleep_inc"))
    sleep_max = int(addon.getSetting("sleep_max"))
    sleep_str = getSleepCycle()
    if sleep_str == "":
        sleep = -1
    else:
        sleep = int(sleep_str)
    if sleep == -1:
        sleep = 0 + sleep_inc
    else:
        sleep = sleep + sleep_inc
        if sleep > sleep_max:
            sleep = -1
            
    setSleepCycle(sleep)
    if sleep == -1:
        showSleepBox("Sleep Timer", "Timer off")
    else:
        showSleepBox("Sleep Timer", str(sleep) + " minutes")
    
def setSleepCycle(value):
    xbmcgui.Window(10000).setProperty("Zomboided_Sleep_Cycle", str(value))
    return

def getSleepCycle():
    return xbmcgui.Window(10000).getProperty("Zomboided_Sleep_Cycle")



    
# Call the common cycle routine
debugTrace("-- Entered cycle.py --")
requestSleepCycle()
debugTrace("-- Exit cycle.py --")
