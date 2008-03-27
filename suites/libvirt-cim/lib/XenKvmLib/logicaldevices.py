#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
#

import os
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL, SKIP

# The list_values that is passed should be of the type ..
#     disk  = {
#              'SystemName'        : test_dom, \
#              'CreationClassName' : "Xen_LogicalDisk", \
#              'DeviceID'          : "%s/%s" % (test_dom,test_disk), \
#              'Name'              : test_disk
#            }
#     proc = { 'SystemName'        : test_dom,
#               ......
#            }
#     net  = { ...} 
#     disk = { ...} 
#
#
#        eaf_values = {  "Xen_Processor"   : proc, \
#                        "Xen_LogicalDisk" : disk, \
#                        "Xen_NetworkPort" : net, \
#                        "Xen_Memory"      : mem
#                  }
# Reference tc: HostSystem/04_hs_to_EAPF.py 

def field_err(assoc_info, field_list, fieldname):
    logger.error("%s Mismatch", fieldname)
    logger.error("Returned %s instead of %s", assoc_info[fieldname], field_list[fieldname])

def spec_err(fieldvalue, field_list, fieldname):
    logger.error("%s Mismatch", fieldname)
    logger.error("Returned %s instead of %s", fieldvalue, field_list[fieldname])

def verify_proc_values(assoc_info, list_values):
    proc_values = list_values['Xen_Processor']
    if assoc_info['CreationClassName'] != proc_values['CreationClassName']:
        field_err(assoc_info, proc_values, fieldname = 'CreationClassName')
        return FAIL 
    if assoc_info['DeviceID'] != proc_values['DeviceID']:
        field_err(assoc_info, proc_values, fieldname = 'DeviceID')
        return FAIL 
    sysname = assoc_info['SystemName']
    if sysname != proc_values['SystemName']:
        spec_err(sysname, proc_values, fieldname = 'SystemName')
        return FAIL 
    return PASS

def verify_mem_values(assoc_info, list_values):
    mem_values = list_values['Xen_Memory']
    if assoc_info['CreationClassName'] != mem_values['CreationClassName']:
        field_err(assoc_info, mem_values, fieldname = 'CreationClassName')
        return FAIL 
    if assoc_info['DeviceID'] != mem_values['DeviceID']:
        field_err(assoc_info, mem_values, fieldname = 'DeviceID')
        return FAIL 
    sysname = assoc_info['SystemName']
    if sysname != mem_values['SystemName']:
        spec_err(sysname, mem_values, fieldname = 'SystemName')
        return FAIL 
    blocks = ((int(assoc_info['NumberOfBlocks'])*4096)/1024)
    if blocks != mem_values['NumberOfBlocks']:
        spec_err(blocks, mem_values, fieldname = 'NumberOfBlocks')
        return FAIL 
    return PASS

def verify_net_values(assoc_info, list_values):
    net_values = list_values['Xen_NetworkPort']
    if assoc_info['CreationClassName'] != net_values['CreationClassName']:
        field_err(assoc_info, net_values, fieldname = 'CreationClassName')
        return FAIL 
    if assoc_info['DeviceID'] != net_values['DeviceID']:
        field_err(assoc_info, net_values, fieldname = 'DeviceID')
        return FAIL 
    sysname = assoc_info['SystemName']
    if sysname != net_values['SystemName']:
        spec_err(sysname, net_values, fieldname = 'SystemName')
        return FAIL 
# We are assinging only one mac address and hence we expect only one 
# address in the list
    netadd = assoc_info['NetworkAddresses'][0]
    if netadd != net_values['NetworkAddresses']:
        spec_err(netadd, net_values, fieldname = 'NetworkAddresses')
        return FAIL 
    return PASS

def verify_disk_values(assoc_info, list_values):
    disk_values = list_values['Xen_LogicalDisk']
    if assoc_info['CreationClassName'] != disk_values['CreationClassName']:
        field_err(assoc_info, disk_values, fieldname = 'CreationClassName')
        return FAIL 
    if assoc_info['DeviceID'] != disk_values['DeviceID']:
        field_err(assoc_info, disk_values, fieldname = 'DeviceID')
        return FAIL 
    sysname = assoc_info['SystemName']
    if sysname != disk_values['SystemName']:
        spec_err(sysname, disk_values, fieldname = 'SystemName')
        return FAIL 
    devname = assoc_info['Name']
    if devname != disk_values['Name']:
        spec_err(devname, disk_values, fieldname = 'Name')
        return FAIL 
    return PASS

