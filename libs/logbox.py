#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2016 Zomboided
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
#    This module will display a log box on the screen

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
from libs.utility import debugTrace, errorTrace, infoTrace, newPrint


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
            

def showLogBox(caption, text):
    path = xbmcaddon.Addon("service.zomboided.tools").getAddonInfo("path")
    win = LogBox("logtextbox.xml", path, caption=caption, text=text)
    win.doModal()
    del win
    

def popupKodiLog():
    dialog_text = ""
    try:
        log_file = open(xbmcvfs.translatePath("special://logpath/kodi.log"), 'r', errors='ignore')
        log_output = log_file.readlines()
        log_file.close()    
        for line in log_output:
            dialog_text = dialog_text + line
    except:
        dialog_text = "Log file " + xbmcvfs.translatePath("special://logpath/kodi.log") + " weirdly does not exist...maybe try rebooting?"
    showLogBox("Kodi Log", dialog_text)
