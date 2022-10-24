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
#    Shared code fragments

import xbmc
import xbmcaddon
import time

forceDebug = False

DEC_ERR = "*** DECODE ERROR *** : "

def ifDebug():
    if forceDebug: return True
    if xbmcaddon.Addon("service.zomboided.tools").getSetting("enable_debug") == "true":
        return True
    return False

    
def setDebug(debug):
    global forceDebug
    forceDebug = debug
    
    
def debugTrace(data):    
    try:
        if ifDebug():
            log = "ZTools : Debug: " + str(data)
            xbmc.log(msg=log, level=xbmc.LOGINFO)       
        else:
            log = "ZTools : " + str(data)
            xbmc.log(msg=log, level=xbmc.LOGDEBUG)
    except Exception as e:
        log = DEC_ERR + "ZTools : " + str(data)
        log = log.encode('ascii', 'ignore')
        xbmc.log(msg=log, level=xbmc.LOGERROR)        


def alwaysTrace(data):
    try:
        log = "ZTools : Forced: " + str(data)
        xbmc.log(msg=log, level=xbmc.LOGINFO)       
    except Exception as e:
        log = DEC_ERR + "ZTools : " + str(data)
        log = log.encode('ascii', 'ignore')
        xbmc.log(msg=log, level=xbmc.LOGERROR)        
    
    
def errorTrace(module, data):
    try:
        log = "ZTools : (" + module + ") " + str(data)
        xbmc.log(msg=log, level=xbmc.LOGERROR)
    except Exception as e:
        log = DEC_ERR + "ZTools : " + str(data)
        log = log.encode('ascii', 'ignore')
        xbmc.log(msg=log, level=xbmc.LOGERROR)        
    
    
def infoTrace(module, data):
    try:
        log = "ZTools : (" + module + ") " + str(data)
        xbmc.log(msg=log, level=xbmc.LOGINFO)
    except Exception as e:
        log = DEC_ERR + "ZTools : " + str(data)
        log = log.encode('ascii', 'ignore')
        xbmc.log(msg=log, level=xbmc.LOGERROR) 

    
def infoPrint(data):
    try:
        xbmc.log(msg=str(data), level=xbmc.LOGINFO)
    except Exception as e:
        log = DEC_ERR + str(data)
        log = log.encode('ascii', 'ignore')
        xbmc.log(msg=log, level=xbmc.LOGERROR)


def newPrint(data):
    xbmc.log(msg=str(data), level=xbmc.LOGINFO)

   
def now():
    return int(time.time())
    

def enum(**enums):
    return type('Enum', (), enums)    
    