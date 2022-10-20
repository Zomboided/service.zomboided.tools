#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2018 Zomboided
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
#    Test the file transfer speed over a LAN

import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
import os
import time
from libs.utility import debugTrace, errorTrace, infoTrace, newPrint

one_mb = 1048576

def formatFileSize(size_bytes):
    if size_bytes > 1047527424: #1GB
        size_gb = (float(size_bytes))/1024/1024/1024
        return '{:.3f}'.format(size_gb) + "GB"
    if size_bytes > 1048576: #1MB
        return str(int((size_bytes/1024)/1024)) + "MB"
    return str(size_bytes/1024) + "KB"
    
    
def speedTest():
    # Set the addon name for use in the dialogs
    addon = xbmcaddon.Addon("service.zomboided.tools")
    addon_name = addon.getAddonInfo("name")
    
    # Get the name of the file we're reading
    source = addon.getSetting("speed_test_source")
    dialog = xbmcgui.Dialog()
    source = dialog.browse(1, "Choose >50MB file to test LAN speed", 'files', '', False, False, '')

    if source == "": return
    
    # Reading in 32k blocks as a good average.  Don't know how to work out what the 
    # actual value is for the file system the source file is located at. 
    chunk_size=32768
    if not xbmcvfs.exists(source):
        errorTrace("speedtest.py", "Source file does not exist " + source)
        xbmcgui.Dialog().ok(addon_name, "Source file does not exist\nFile : " + source)
    else:
        # Open the file and get the size of it
        
        try:
            debugTrace("Opening file " + source)
            f = open(source, "rb")
            total_size = os.path.getsize(source)
        except:
            errorTrace("speedtest.py", "Error opening file " + source)
            total_size = -1

        # Only run the test if the file is bigger than 50MB
        if total_size > (one_mb * 50):
            infoTrace("speedtest.py", "Running speed test with " + source)
            progress = xbmcgui.DialogProgress()
            progress_title = "Running speed test"
            progress.create(addon_name,progress_title) 

            total_read = 0
            total_to_mb = 0
            percent = 0
            time_start = time.time()
            last_time = time_start
            transfer_speed = 0
            
            bytes_read = f.read(chunk_size)
            while bytes_read:
                bytes_read = f.read(chunk_size)
                total_read = total_read + chunk_size
                total_to_mb = total_to_mb + chunk_size
                if total_to_mb >= one_mb:
                    total_to_mb = total_to_mb - one_mb
                    percent = percent + 1
                    time_now = time.time()-time_start
                    progress_message = "Read " + formatFileSize(total_read) + " in " + '{:.0f}'.format(time_now) + " seconds"            
                    if percent == 100:                
                        last_time = time.time() - last_time
                        transfer_speed = ((one_mb * 800) / last_time) / 1000000                
                        progress_title = "Running speed test  (100MB average " + '{:.2f}'.format(transfer_speed) + "Mbps)"
                        last_time = time.time()
                        percent = 0
                    progress.update(percent, progress_title + "\n" + progress_message)
                if progress.iscanceled() : break
            f.close()

            progress.close()

            time_now = time.time()
            transfer_speed = (total_read * 8 / (time_now - time_start)) / 1000000 
            per_hour = (total_read / (time_now - time_start)) * 60 * 60
            
            if (time_now - time_start) >= 60:
                xbmcgui.Dialog().ok(addon_name, "Read " + formatFileSize(total_read) + " in " + '{:.0f}'.format(time_now - time_start) + " seconds, average of " + '{:.2f}'.format(transfer_speed) + "Mbps.\nEquivalent to " + formatFileSize(per_hour) + " per hour.\nConsider running the test during different network loads.")
            else:
                xbmcgui.Dialog().ok(addon_name, "Read " + formatFileSize(total_read) + " in " + '{:.0f}'.format(time_now - time_start) + " seconds, average of " + '{:.2f}'.format(transfer_speed) + "Mbps.\nEquivalent to " + formatFileSize(per_hour) + " per hour.\nRun test for longer for better accuracy.")
        else:
            if total_size < 0:
                debugTrace("Could not open source file")
                xbmcgui.Dialog().ok(addon_name, "Could not open source file.")
            else:
                debugTrace("Source file is too small (" + str(total_size) + ")")
                xbmcgui.Dialog().ok(addon_name, "Run the test with a file that's at least 50MB.\nFile is " + formatFileSize(total_size))
        

