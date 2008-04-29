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

import sys
from CimTest import Globals 
from CimTest.Globals import log_param, logger
from CimTest.ReturnCodes import FAIL, PASS

pasd_cn = 'ProcResourceAllocationSettingData'
nasd_cn = 'NetResourceAllocationSettingData'
dasd_cn = 'DiskResourceAllocationSettingData'
masd_cn = 'MemResourceAllocationSettingData'

def CCN_err(assoc_info, list):
    Globals.logger.error("%s Mismatch", 'CreationClassName')
    Globals.logger.error("Returned %s instead of %s", \
         assoc_info['CreationClassName'], list['CreationClassName'])
    
def RType_err(assoc_info, list):
    Globals.logger.error("%s Mismatch", 'ResourceType')
    Globals.logger.error("Returned %s instead of %s", \
         assoc_info['ResourceType'], list['ResourceType'])

def InstId_err(assoc_info, list):
    Globals.logger.error("%s Mismatch", 'InstanceID')
    Globals.logger.error("Returned %s instead of %s", \
         assoc_info['InstanceID'], list['InstanceID'])

def verify_procrasd_values(assoc_info, procrasd_list):
    status = PASS
    if assoc_info['InstanceID'] != procrasd_list['InstanceID']:
        InstId_err(assoc_info, procrasd_list)
        status = FAIL
    if assoc_info['ResourceType'] != procrasd_list['ResourceType']:
        RType_err(assoc_info, procrasd_list)
        status = FAIL
    return status

def verify_netrasd_values(assoc_info, netrasd_list):
    status = PASS
    if assoc_info['InstanceID'] != netrasd_list['InstanceID']:
        InstId_err(assoc_info, netrasd_list)
        status = FAIL
    if assoc_info['ResourceType'] != netrasd_list['ResourceType']:
        RType_err(assoc_info, netrasd_list)
        status = FAIL
    if assoc_info['NetworkType'] != netrasd_list['ntype1'] and \
       assoc_info['NetworkType'] != netrasd_list['ntype2']:
        Globals.logger.error("%s Mismatch", 'NetworkType')
        Globals.logger.error("Returned %s instead of %s or %s", \
                             assoc_info['NetworkType'], netrasd_list['ntype1'],
                             netrasd_list['ntype2'])
        status = FAIL
    return status

def verify_diskrasd_values(assoc_info, diskrasd_list):
    status = PASS
    if assoc_info['InstanceID'] != diskrasd_list['InstanceID']:
        InstId_err(assoc_info, diskrasd_list)
        status = FAIL
    if assoc_info['ResourceType'] != diskrasd_list['ResourceType']:
        RType_err(assoc_info, diskrasd_list)
        status = FAIL
    if assoc_info['Address'] != diskrasd_list['Address']:
        Globals.logger.error("%s Mismatch", 'Address')
        Globals.logger.error("Returned %s instead of %s ", \
              assoc_info['Address'], diskrasd_list['Address'])
        status = FAIL
    return status

def verify_memrasd_values(assoc_info, memrasd_list):
    status = PASS
    if assoc_info['InstanceID'] != memrasd_list['InstanceID']:
        InstId_err(assoc_info, memrasd_list)
        status = FAIL
    if assoc_info['ResourceType'] != memrasd_list['ResourceType']:
        RType_err(assoc_info, memrasd_list)
        status = FAIL
    if assoc_info['AllocationUnits'] != memrasd_list['AllocationUnits']:
        Globals.logger.error("%s Mismatch", 'AllocationUnits')
        Globals.logger.error("Returned %s instead of %s ", \
              assoc_info['AllocationUnits'],  memrasd_list['AllocationUnits'])
        status = FAIL 
    if assoc_info['VirtualQuantity'] != memrasd_list['VirtualQuantity']:
        Globals.logger.error("%s mismatch", 'VirtualQuantity')
        Globals.logger.error("Returned %s instead of %s ", \
              assoc_info['VirtualQuantity'], memrasd_list['VirtualQuantity'])
        status = FAIL 
    return status
