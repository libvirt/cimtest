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
from CimTest.Globals import log_param, logger
from CimTest.ReturnCodes import FAIL, PASS
from XenKvmLib import vxml
from XenKvmLib.classes import get_typed_class


pasd_cn = 'ProcResourceAllocationSettingData'
nasd_cn = 'NetResourceAllocationSettingData'
dasd_cn = 'DiskResourceAllocationSettingData'
masd_cn = 'MemResourceAllocationSettingData'
proccn =  'Processor'
memcn  =  'Memory'
netcn  =  'NetworkPort'
diskcn =  'LogicalDisk'

def rasd_init_list(vsxml, virt, t_disk, t_dom, t_mac, t_mem):
    """
        Creating the lists that will be used for comparisons.
    """
    rasd_values =  { }
    proc_cn = get_typed_class(virt, proccn)
    mem_cn = get_typed_class(virt, memcn)
    net_cn = get_typed_class(virt, netcn)
    disk_cn = get_typed_class(virt, diskcn)

    in_list = { 'proc'  :      proc_cn,
                 'mem'  :      mem_cn,
                 'net'  :      net_cn,
                 'disk' :      disk_cn
               }
    try:

        disk_path = vsxml.xml_get_disk_source()

        rasd_values = { 
                        proc_cn  : {
                                     "InstanceID"   : '%s/%s' %(t_dom, "proc"),
                                     "ResourceType" : 3,
                                    }, 
                        disk_cn  : {
                                     "InstanceID"   : '%s/%s' %(t_dom, t_disk), 
                                     "ResourceType" : 17, 
                                     "Address"      : disk_path, 
                                    }, 
                        net_cn   : {
                                    "InstanceID"   : '%s/%s' %(t_dom, t_mac), 
                                    "ResourceType" : 10 , 
                                    "ntype"        : [ 'bridge', 'user',
                                                         'network', 'ethernet'] 
                                      }, 
                        mem_cn   : {
                                    "InstanceID" : '%s/%s' %(t_dom, "mem"), 
                                    "ResourceType"    : 4, 
                                    "AllocationUnits" : "KiloBytes",
                                    "VirtualQuantity" : (t_mem * 1024),
                                  }
                      } 
    except Exception, details:
        logger.error("Exception: In fn rasd_init_list %s", details)
        return FAIL, rasd_values, in_list

    nettype   = vsxml.xml_get_net_type()
    if not nettype in rasd_values[net_cn]['ntype']:
        logger.info("Adding the %s net type", nettype)
        rasd_values[net_cn]['ntype'].append(nettype)

    return PASS, rasd_values, in_list

def CCN_err(assoc_info, list):
    logger.error("%s Mismatch", 'CreationClassName')
    logger.error("Returned %s instead of %s", 
                  assoc_info['CreationClassName'], list['CreationClassName'])
    
def RType_err(assoc_info, list):
    logger.error("%s Mismatch", 'ResourceType')
    logger.error("Returned %s instead of %s", 
                  assoc_info['ResourceType'], list['ResourceType'])

def InstId_err(assoc_info, list):
    logger.error("%s Mismatch", 'InstanceID')
    logger.error("Returned %s instead of %s", 
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
    if not assoc_info['NetworkType'] in netrasd_list['ntype']:
        logger.error("%s Mismatch", 'NetworkType')
        logger.error("Returned '%s' instead of returning one of %s types",
                      assoc_info['NetworkType'], netrasd_list['ntype'])
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
        logger.error("%s Mismatch", 'Address')
        logger.error("Returned %s instead of %s ", 
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
        logger.error("%s Mismatch", 'AllocationUnits')
        logger.error("Returned %s instead of %s ", 
                     assoc_info['AllocationUnits'], 
                     memrasd_list['AllocationUnits'])
        status = FAIL 
    if assoc_info['VirtualQuantity'] != memrasd_list['VirtualQuantity']:
        logger.error("%s mismatch", 'VirtualQuantity')
        logger.error("Returned %s instead of %s ", 
                      assoc_info['VirtualQuantity'], 
                      memrasd_list['VirtualQuantity'])
        status = FAIL 
    return status
