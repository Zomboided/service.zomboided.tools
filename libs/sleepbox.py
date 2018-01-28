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
#    This module will display the sleep timer on the screen

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
from utility import debugTrace, errorTrace, infoTrace


ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92


# Class to display a box with an ok and refresh, a close, and a big pane full of small text
class LogBox(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.caption = kwargs.get("caption", "")
        self.text = kwargs.get("text", "")
        xbmcgui.WindowXMLDialog.__init__(self)

    def onInit(self):
        self.getControl(100).setLabel(self.caption)
        self.getControl(200).setText(self.text)

    def onAction(self, action):
        actionId = action.getId()
        if actionId in [ACTION_PREVIOUS_MENU, ACTION_NAV_BACK]:
            return self.close()
            

def showSleepBox(caption, text):
    path = xbmcaddon.Addon("service.zomboided.tools").getAddonInfo("path")
    win = LogBox("sleepbox.xml", path, caption=caption, text=text)
    win.doModal()
    del win
 

      
