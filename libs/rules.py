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
import urllib2
from libs.utility import debugTrace, errorTrace, infoTrace, newPrint
from libs.vpnapi import VPNAPI


VIDEO_GROUP = "Video"
EMBY_GROUP = "Emby"
WILDCARD = "[I]All[/I]"

RULES_PATH = xbmc.translatePath("special://home/addons/service.zomboided.tools/RULES.txt")
USER_RULES_PATH = xbmc.translatePath("special://home/userdata/addon_data/service.zomboided.tools/RULES.txt")


def parseRulesString(rule):
    # Group; Number; Addon Title; Addon Function; Addon Name; Commands;
    tokens = rule.split(";")
    if len(tokens) < 6:
        raise Exception("Could not parse rule " + rule)
    else:
        commands = []
        for i in range(5, len(tokens)):
            commands.append(tokens[i].strip(" \t\n\r"))
        return tokens[0].strip(" "), tokens[1].strip(" "), tokens[2].strip(" "), tokens[3].strip(" "), tokens[4].strip(" "), commands


# As part of initialisation, these window properties will be pre populated so that can be called
# from the addon.py module without having to create a rules object each time.  They could be
# expanded to take a mask and determine if it's part of the comma separated string that's stored
# but right now there's no need for that
def hasVideoAddons():
    if xbmcgui.Window(10000).getProperty("Zomboided_Tools_Emby_Addons") == "": return False
    return True

def hasEmbyAddons():
    if xbmcgui.Window(10000).getProperty("Zomboided_Tools_Video_Addons") == "": return False
    return True


class rules:          

    def __init__(self, fetch_from_git):
        self.rules = None
        self.addon = xbmcaddon.Addon("service.zomboided.tools")
        self.addon_name = self.addon.getAddonInfo("name")
        if fetch_from_git: self.getGitRules()
        self.parseRulesFiles(self.readRulesFiles())
        addons = self.getRulesAddons("")
        rule_addons = ""
        for a in addons:
            if not rule_addons == "": rule_addons = rule_addons + ","
            rule_addons = rule_addons + a

            
    def getGitRules(self):
        if self.addon.getSetting("refresh_rules") == "true":
            # Download RULES.txt file from Github
            for i in range(0, 6):
                try:
                    debugTrace("Getting rules from Github")
                    download_url = "https://raw.githubusercontent.com/Zomboided/service.zomboided.tools/master/RULES.txt"
                    download_url = download_url.replace(" ", "%20")
                    download_rules = urllib2.urlopen(download_url)
                    break
                except urllib2.HTTPError as e:
                    errorTrace("rules.py", "Can't get the rules from Github")
                    errorTrace("rules.py", "API call was " + download_url)
                    errorTrace("rules.py", "Response was " + str(e.code) + " " + e.reason)
                    errorTrace("rules.py", e.read())
                except Exception as e:
                    errorTrace("rules.py", "Can't get the rules from Github")
                    errorTrace("rules.py", "API call was " + download_url)
                    errorTrace("rules.py", "Response was " + str(type(e)) + " " + str(e))
                finally:
                    # Give up if this is the last time round
                    if i == 5: 
                        errorTrace("rules.py", "Can't get rules from Github, using existing set")
                        return
                    # Otherwise wait 30 seconds before trying to get the rules again
                    xbmc.sleep(30000)
            try:
                # Overwrite RULES.txt
                output = open(RULES_PATH, 'w')
                for r in download_rules:
                    output.write(r)
                output.close()
                infoTrace("rules.py", "Updated the rules file from GitHub")
            except Exception as e:
                errorTrace("rules.py", "Couldn't write the rules files downloaded from Github")
                errorTrace("rules.py", str(e))
            
            
    def readRulesFiles(self):
        # Read the rules file
        if xbmcvfs.exists(RULES_PATH):
            try:
                debugTrace("Reading rules file " + RULES_PATH)
                rules_file = open(RULES_PATH, 'r')
                rules = rules_file.readlines()
                rules_file.close()        
            except Exception as e:
                errorTrace("rules.py", "Couldn't open rules file " + RULES_PATH)
                errorTrace("rules.py", str(e))
                rules = None
        else:
            errorTrace("rules.py", "File " + RULES_PATH + " doesn't exist")
        # Read the user rules file
        user_rules = None
        if xbmcvfs.exists(USER_RULES_PATH):
            try:
                debugTrace("Reading user rules file " + USER_RULES_PATH)
                user_rules_file = open(USER_RULES_PATH, 'r')
                user_rules = user_rules_file.readlines()
                user_rules_file.close()        
            except Exception as e:
                errorTrace("rules.py", "Couldn't open rules file " + USER_RULES_PATH)
                errorTrace("rules.py", str(e))
                user_rules = None
        # Add the user rules file to the end of the rules file
        if not user_rules == None:
            if rules == None:
                rules = user_rules
            else:
                for u in user_rules:
                    rules.append(u)
        return rules

        
    def parseRulesFiles(self, rules):
        # Parse the rules file
        self.rules = []
        rule_numbers = []
        self.groups = []
        group_active = False
        current_group = ""
        if not rules == None:
            rule = ""
            try:
                debugTrace("Parsing rules file")
                for r in rules:
                    rule = r.strip(" \t\n\r")
                    # Groups
                    if rule.startswith("[") and rule.endswith("]"):
                        if rule[1] == "/":
                            # Group end
                            group_active = False
                            current_group = ""
                        else:
                            # Group start
                            group_active = True
                            group = rule[1:rule.index("]")]
                            current_group = group
                            if not group in self.groups:
                                self.groups.append(group)
                        rule = ""
                    # Comments
                    if rule.startswith("#"):
                        rule = ""
                    # Repeat
                    found_repeat = False
                    if rule.startswith("+"):
                        repeat_rule = rule[1:(rule.index(";")+1)]
                        for repeat in rules:
                            if repeat.startswith(repeat_rule):
                                rule = repeat
                                found_repeat = True
                                break                  
                        if not found_repeat:
                            rule = ""
                    # Try and write rule
                    if not rule == "":
                        number = rule[0:(rule.index(";"))]
                        if not found_repeat and number in rule_numbers:
                            # Rule or rules with the same number already exists, just update them
                            i = 0
                            for replace in self.rules:
                                rule_group, rule_number, rule_title, rule_function, rule_addon, commands = parseRulesString(replace)
                                if number == rule_number:
                                    self.rules[i] = rule_group + "; " + rule
                                    debugTrace("Replacing " + replace + " with " + rule)
                                i += 1   
                        else:
                            # Write rule if it's part of a group
                            if group_active:
                                self.rules.append(current_group + "; " + rule)
                                rule_numbers.append(number)
                                debugTrace("Found " + rule + " in " + current_group)
                            else:
                                errorTrace("rules.py", "Excluded rule " + rule + " as it is not in a group")
            except Exception as e:                        
                errorTrace("rules.py", "Couldn't parse rules files, last line read was '" + rule + "'")
                errorTrace("rules.py", str(e))

                
    def getReadableRules(self, group_mask, selected_mask):
        # Return a human readable rules list which are part of the group_mask. The 
        # selected_mask will be used to highlight which rules were selected previously.
        selected_rules = []
        if not selected_mask == "":
            selected_rules = selected_mask.split(",")
        group_filter = []
        if not group_mask == "":
            group_filter = group_mask.split(",")
        ret_list = []
        for rule in self.rules:
            rule_group, rule_number, rule_title, rule_function, rule_addon, commands = parseRulesString(rule)
            if xbmc.getCondVisibility("System.HasAddon(" + rule_addon + ")"):
                if len(group_filter) == 0 or rule_group in group_filter:
                    if (len(selected_rules) > 0 and rule_number in selected_rules):
                        start_tag = "[B]"
                        end_tag = "[/B]"
                    else:
                        start_tag = ""
                        end_tag = ""
                    ret_list.append(start_tag + rule_number + ". " + rule_title + ", " + rule_function + end_tag)
        return ret_list
        
        
    def getRules(self, group_mask, rules_mask):
        # Return the rules which are part of the group_mask
        allowed_rules = []
        if not rules_mask == "":
            allowed_rules = rules_mask.split(",")        
        group_filter = []
        if not group_mask == "":
            group_filter = group_mask.split(",")
        ret_list = []
        for rule in self.rules:
            rule_group, rule_number, rule_title, rule_function, rule_addon, commands = parseRulesString(rule)
            if xbmc.getCondVisibility("System.HasAddon(" + rule_addon + ")"):
                if len(group_filter) == 0 or rule_group in group_filter:
                    if (len(allowed_rules) == 0 or rule_number in allowed_rules):
                        ret_list.append(rule)
        return ret_list
        
        
    def getRulesAddons(self, group_mask):
        # Return a list of the active addons the rules are using, within the groups in the group_mask
        # Addons that have been disabled will not be returned
        group_filter = []
        if not group_mask == "":
            group_filter = group_mask.split(",")
        ret_list = []
        for rule in self.rules:
            rule_group, rule_number, rule_title, rule_function, rule_addon, commands = parseRulesString(rule)
            if xbmc.getCondVisibility("System.HasAddon(" + rule_addon + ")"):
                if len(group_filter) == 0 or rule_group in group_filter:
                    if not rule_addon in ret_list: 
                        ret_list.append(rule_addon)
        return ret_list    
        

    def preloadRulesAddons(self):
        # This pre-loads windows properties with the list of video and Emby add-ons
        # These are used to determine whether to display menu items efficiently
        group_filter = []
        emby_string = ""
        video_string = ""
        for rule in self.rules:
            rule_group, rule_number, rule_title, rule_function, rule_addon, commands = parseRulesString(rule)
            if xbmc.getCondVisibility("System.HasAddon(" + rule_addon + ")"):
                if rule_group == EMBY_GROUP:
                    if not emby_string == "": emby_string = emby_string + ","
                    emby_string = emby_string + rule_addon
                if rule_group == VIDEO_GROUP:
                    if not video_string == "": video_string = video_string + ","
                    video_string = video_string + rule_addon
        xbmcgui.Window(10000).setProperty("Zomboided_Tools_Emby_Addons", emby_string)
        xbmcgui.Window(10000).setProperty("Zomboided_Tools_Video_Addons", video_string)
        

    def getRulesGroups(self, selected_mask):
        # Return all of the groups in the rules files
        selected_groups = []
        if not selected_mask == "":
            selected_groups = selected_mask.split(",")
        ret_list = []
        for group in self.groups:
            if (len(selected_groups) > 0 and group in selected_groups):
                start_tag = "[B]"
                end_tag = "[/B]"
            else:
                start_tag = ""
                end_tag = ""
            ret_list.append(start_tag + group + end_tag)    
        return ret_list

        
    def runRules(self, dialogs, group_mask, rules_mask):

        try:
            comm_delay = int(self.addon.getSetting("command_delay"))*1000
        except:
            comm_delay = 10000
        #comm_delay = 1000
        
        if (not dialogs or xbmcgui.Dialog().yesno(self.addon_name, "About to take over the Kodi GUI.\n[B]You must avoid any input[/B] until the process is finished.\nAre you sure you want to continue?")):

            api = None
            if xbmc.getCondVisibility("System.HasAddon(service.vpn.manager)"):
                try:
                    api = VPNAPI()
                except Exception as e:
                    errorTrace("service.py", "Couldn't connect to the VPN API")
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
            
            rules = self.getRules(group_mask, rules_mask)
            
            if len(rules) > 0:
                
                percent = 0
                percent_inc = (100/(len(rules) + percent_adjust))
                
                # Pause the VPN filtering
                if not api == None: 
                    percent += percent_inc
                    progDiag.update(percent, "Pausing VPN filtering")           
                    api.pause()
                xbmc.sleep(comm_delay)
                
                debugTrace("Running commands, rules group is " + group_mask + " and mask is " + rules_mask)
                for rule in rules:
                    rule_group, rule_number, rule_title, rule_function, rule_addon, commands = parseRulesString(rule)
                    debugTrace("Rule string is " + rule)
                    percent += percent_inc
                    if xbmc.getCondVisibility("System.HasAddon(" + rule_addon + ")"):
                        progDiag.update(percent, "Running " + rule_title + ", " + rule_function)
                        infoTrace("rules.py", "Running " + rule_number + ", " + rule_title + ", " + rule_function)
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
                                errorTrace("rules.py", "Couldn't run command " + command)
                                errorTrace("rules.py", str(e))
                                progDiag.update(percent, "[B]Error running command, check log[/B]")    
                    else:
                        progDiag.update(percent, "Checking installed add-ons")
                        debugTrace("Couldn't find addon " + rule_addon)
                        xbmc.sleep(300)
                
                # Restart the VPN filtering
                if not api == None: 
                    percent += percent_inc
                    progDiag.update(percent, "Restarting VPN filtering")           
                    api.restart()
                    xbmc.sleep(comm_delay)           
                    
                progDiag.update(100, "Finished running rules", " ")
                xbmc.sleep(2000)
            else:
                progDiag.update(100, "Couldn't find any rules for installed add-ons", " ")
                xbmc.sleep(5000)
                
            progDiag.close() 
            xbmc.sleep(1000)                    
