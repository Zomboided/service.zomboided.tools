#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2017 Zomboided
#
#    Connection script called by the VPN Manager for OpenVPN settings screen
#    to validate a connection to a VPN provider.
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
import xbmcvfs
import datetime
import os
from libs.utility import debugTrace, errorTrace, infoTrace, newPrint
from libs.cache import clearCache

action = sys.argv[1]

debugTrace("-- Entered clearcache.py with parameter " + action + " --")

clearCache(0)

if action == "settings":   
    xbmc.executebuiltin("Addon.OpenSettings(service.zomboided.tools)")    

debugTrace("-- Exit clearcache.py --")
