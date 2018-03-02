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
#    This module pops up a screen with some log info.

import xbmcaddon
import xbmcgui
from libs.utility import debugTrace, errorTrace, infoTrace, newPrint
from libs.rules import rules, VIDEO_GROUP, EMBY_GROUP, WILDCARD

trigger = sys.argv[1]
action = sys.argv[2]

RULES = "rules"
GROUPS = "groups"
    
def showList(list, filter, type):
    groups = ""
    if len(list) > 0:
        selected = xbmcgui.Dialog().multiselect("Select all active " + type + ", current in bold", list)
        if not selected == None:
            for i in selected:
                if not groups == "": groups = groups + ","
                if type == GROUPS:                    
                    groups = groups + list[int(i)]
                else:
                    groups = groups + list[int(i)][0:list[int(i)].index(".")]
            groups = groups.replace("[B]", "")
            groups = groups.replace("[/B]", "")
        else:
            return None
    else:
        if type == "groups":
            xbmcgui.Dialog().ok(addon_name, "No groups were found, assuming all rules.")
        else:
            if filter == "":
                xbmcgui.Dialog().ok(addon_name, "No rules were found for the enabled add-ons.")
            else:
                xbmcgui.Dialog().ok(addon_name, "No rules were found in group(s) " + filter + " for the enabled add-ons.")
    return groups


debugTrace("-- Entered filtering.py with parameters " + trigger + ", " + action + " --")

# Set the addon name for use in the dialogs
addon = xbmcaddon.Addon("service.zomboided.tools")
addon_name = addon.getAddonInfo("name")

rules = rules(False)

list = []

if action == "Video":
    mask = addon.getSetting("video_mask")
    if mask == WILDCARD: mask = ""
    list = rules.getReadableRules(VIDEO_GROUP, mask)
    mask = showList(list, action, RULES)
    if not mask == None: 
        if mask == "": mask = WILDCARD
        addon.setSetting("video_mask", mask)
    
elif action == "Emby":
    mask = addon.getSetting("emby_mask")
    if mask == WILDCARD: mask = ""
    list = rules.getReadableRules(EMBY_GROUP, mask)
    mask = showList(list, action, RULES)
    if not mask == None: 
        if mask == "": mask = WILDCARD
        addon.setSetting("emby_mask", mask)

elif action == "Rules":
    mask = addon.getSetting(addon.getSetting("action_rules_mask_" + trigger))
    if mask == WILDCARD: mask = ""
    list = rules.getReadableRules(addon.getSetting("action_rules_group_" + trigger), mask)
    mask = showList(list, addon.getSetting("action_rules_group_" + trigger), RULES)
    if not mask == None:
        if mask == "": mask = WILDCARD
        addon.setSetting("action_rules_mask_" + trigger, mask)

elif action == "Set":
    list = rules.getRulesGroups(addon.getSetting("action_rules_group_" + trigger))
    mask = showList(list, "", GROUPS)
    if not mask == None: addon.setSetting("action_rules_group_" + trigger, mask)
    
xbmc.executebuiltin("Addon.OpenSettings(service.zomboided.tools)")        
    
debugTrace("-- Exit filtering.py --")
