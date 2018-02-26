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
#    This module runs the rules that can be used to operate the Kodi GUI.

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
from libs.utility import debugTrace, errorTrace, infoTrace, newPrint
from libs.vpnapi import VPNAPI


VIDEO_GROUP = "Video"
EMBY_GROUP = "Emby"
WILDCARD = "[I]All[/I]"

def parseRulesString(rule):
    # Line; Addon Title; Addon Function; Addon Name; Commands;
    tokens = rule.split(";")
    if len(tokens) < 5:
        raise Exception("Could not parse rule " + rule)
    else:
        commands = []
        for i in range(4, len(tokens)):
            commands.append(tokens[i].strip(" \t\n\r"))
        return tokens[0], tokens[1], tokens[2], tokens[3], commands
        

def getRulesStrings(filter_string, allow_repeats):
    # <FIXME> want to allow for a userdata file to add to and overwrite any rules
    # <FIXME> want to download the RULES.txt from Github
    # Load and parse the rules file, filtering the return values by any filter (group) passed in
    rules_path = xbmc.translatePath("special://home/addons/service.zomboided.tools/RULES.txt")
    just_rules = []
    just_groups = []
    filters = []
    if not filter_string == "":
        filters = filter_string.split(",")
    filter_active = True
    command = ""
    if xbmcvfs.exists(rules_path):
        debugTrace("Reading " + rules_path + " with filter " + filter_string)
        try:
            rules_file = open(rules_path, 'r')
            rules = rules_file.readlines()
            rules_file.close()
            filter_active = True
            for r in rules:
                rule = r.strip(" \t\n\r")
                # Find the right rule if this is a repeat tag
                if rule.startswith("+"):
                    if allow_repeats:
                        repeat_rule = rule[1:(rule.index(";"))]
                        repeat_rule = repeat_rule + ";"
                        for repeat in rules:
                            if repeat.startswith(repeat_rule):
                                rule = repeat                
                    else:
                        rule = ""
                if not (rule.startswith("#") or rule == ""):
                    # Look for filters      
                    if rule.startswith("[/") and rule.endswith("]"):
                        if len(filters) > 0 and filter_active:
                            filter_active = False
                    elif rule.startswith("[") and rule.endswith("]"):
                        group = rule[1:rule.index("]")]
                        if not group in just_groups:
                            just_groups.append(group)
                        if len(filters) > 0:
                            filter_active = False
                            for filter in filters:
                                if filter in rule: 
                                    filter_active = True                                    
                    # Use the rule if it's not filtered out                                
                    elif filter_active: 
                        debugTrace("Found rule " + rule)
                        just_rules.append(rule)
                    else:
                        debugTrace("Filter excluded " + rule)
        except Exception as e:                        
            errorTrace("execute.py", "Couldn't read " + rules_path)
            errorTrace("execute.py", "Last line read was '" + rule + "'")
            errorTrace("execute.py", str(e))
    else:
        errorTrace("execute.py", "File " + rules_path + " doesn't exist")
    if len(just_rules) < 1:
        debugTrace("No rules were found in " + rules_path + " for filter " + filter_string)
    if len(just_groups) < 1:
        debugTrace("No groups were found in " + rules_path)
    return just_rules, just_groups


def getReadableRules(filter, rules_mask):
    # Return a human readable rules list, with a filter applied. The rules_mask
    # rules_mask will be used to highlight which rules were selected previously.
    selected_rules = []
    if not rules_mask == "":
        selected_rules = rules_mask.split(",")
    ret_list = []
    rules, _ = getRulesStrings(filter, False)
    for rule_string in rules:
        rule_number, rule_title, rule_function, rule_addon, commands = parseRulesString(rule_string)
        if xbmc.getCondVisibility("System.HasAddon(" + rule_addon + ")"):
            if (len(selected_rules) > 0 and rule_number in selected_rules):
                start_tag = "[B]"
                end_tag = "[/B]"
            else:
                start_tag = ""
                end_tag = ""
            ret_list.append(start_tag + rule_number + ". " + rule_title + ", " + rule_function + end_tag)
    return ret_list


def getRulesAddons(filter):
    # Return a list of the active addons the rules are using, with a filter applied.
    # Addons that have been disabled will not be returned
    ret_list = []
    rules, _ = getRulesStrings(filter, False)
    for rule_string in rules:
        rule_number, rule_title, rule_function, rule_addon, commands = parseRulesString(rule_string)
        if xbmc.getCondVisibility("System.HasAddon(" + rule_addon + ")"):
            if not rule_addon in ret_list: 
                ret_list.append(rule_addon)
    return ret_list    
    

def getRulesGroups(selected_groups):
    # Return all of the groups in the rules file
    ret_list = []
    _, groups = getRulesStrings("", False)
    for group in groups:
        if (len(selected_groups) > 0 and group in selected_groups):
            start_tag = "[B]"
            end_tag = "[/B]"
        else:
            start_tag = ""
            end_tag = ""
        ret_list.append(start_tag + group + end_tag)    
    return ret_list

    
def runRules(dialogs, filter, rules_mask):
    addon = xbmcaddon.Addon("service.zomboided.tools")
    addon_name = addon.getAddonInfo("name")

    allowed_rules = []
    if not rules_mask == "":
        allowed_rules = rules_mask.split(",")
        
    try:
        comm_delay = int(addon.getSetting("command_delay"))*1000
    except:
        comm_delay = 10000

    if (not dialogs or xbmcgui.Dialog().yesno(addon_name, "About to take over the Kodi GUI.\n[B]You must avoid any input[/B] until the process is finished.\nAre you sure you want to continue?")):

        api = None
        if xbmc.getCondVisibility("System.HasAddon(service.vpn.manager)"):
            try:
                api = VPNAPI()
            except Exception as e:
                errorTrace("service.py", "Couldn't connect to the VPN Mgr API")
                errorTrace("service.py", str(e))
                api = None
        
        if api == None:
            percent_adjust = 1
        else:
            percent_adjust = 3
                
        progDiag = xbmcgui.DialogProgressBG()
        progDiag.create("Running commands", "[B]Avoid any input![/B]")
        progDiag.update(0)
        xbmc.sleep(5000)
        
        rules_strings, _ = getRulesStrings(filter, False)
        if not rules_strings == None:
            
            percent = 0
            percent_inc = (100/(len(rules_strings) + percent_adjust))
            
            # Pause the VPN filtering
            if not api == None: 
                percent += percent_inc
                progDiag.update(percent, "Pausing VPN filtering")           
                api.pause()
            xbmc.sleep(comm_delay)
            
            debugTrace("Running commands, rules group is " + filter + " and mask is " + rules_mask)
            for rule in rules_strings:
                rule_number, rule_title, rule_function, rule_addon, commands = parseRulesString(rule)
                debugTrace("Rule string is " + rule)
                percent += percent_inc
                if xbmc.getCondVisibility("System.HasAddon(" + rule_addon + ")"): 
                    if (len(allowed_rules) == 0 or rule_number in allowed_rules):
                        progDiag.update(percent, "Running " + rule_title + ", " + rule_function)
                        infoTrace("execute.py", "Running " + rule_number + ", " + rule_title + ", " + rule_function)
                        xbmc.sleep(2000)
                        comm_percent = float(0)
                        comm_percent_inc = float(percent_inc) / float((len(commands)+1))
                        for command in commands:
                            debugTrace("Executing " + command)
                            comm_percent += comm_percent_inc
                            progDiag.update(percent + int(comm_percent))
                            comm_delay_mod = 1
                            try:
                                if command.startswith("*"):
                                    comm_delay_mod = int(command[1:command.index(" ")])
                                    command = command[command.index(" ") + 1:].strip(" \t\n\r")
                                xbmc.executebuiltin(command)
                                xbmc.sleep(comm_delay * comm_delay_mod)
                            except Exception as e:
                                errorTrace("service.py", "Couldn't run command " + command)
                                errorTrace("service.py", str(e))
                                progDiag.update(percent, "[B]Error running command, check log[/B]")    
                    else:    
                        progDiag.update(percent, "Skipping " + rule_title + ", " + rule_function)
                        debugTrace("Skipping " + rule_title + ", " + rule_function)
                        xbmc.sleep(1000)
                else:
                    progDiag.update(percent, "Looking for addons")
                    debugTrace("Couldn't find addon " + rule_addon)
                    xbmc.sleep(1000)
            
            # Restart the VPN filtering
            if not api == None: 
                percent += percent_inc
                progDiag.update(percent, "Restarting VPN filtering")           
                api.restart()
            xbmc.sleep(comm_delay)
                
            progDiag.update(100, "Finished running rules", " ")
            xbmc.sleep(2000)
        else:
            progDiag.update(100, "Error running rules", "Check the log")
            xbmc.sleep(5000)
            
        progDiag.close() 
        xbmc.sleep(1000)                    
