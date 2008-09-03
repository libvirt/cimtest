#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Veerendra Chandrappa <vechandr@in.ibm.com>
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

#
# This test case is used to reverse verify the Xen_SettingsDefineState class. 
# We use the cross class verification for this.
# First we do the assoc for the Xen_VSSDC class. On the results obtained , we do assoc 
# for the SettingsDefineState class and verify the CreationClassName and the DeviceID's
# returned by the assoc.
#
# For Ex: Command and the fields that are verified are given below. 
#
# wbemcli ain -ac Xen_VirtualSystemSettingDataComponent            
# 'http://localhost:5988/root/virt:Xen_VirtualSystemSettingData.InstanceID="Xen:domgst"'
#
# Output:
# localhost:5988/root/virt:Xen_ProcResourceAllocationSettingData.InstanceID="domgst/0" 
# localhost:5988/root/virt:Xen_NetResourceAllocationSettingData.InstanceID="domgst/00:22:33:aa:bb:cc" 
# localhost:5988/root/virt:Xen_DiskResourceAllocationSettingData.InstanceID="domgst/xvda"
# localhost:5988/root/virt:Xen_MemResourceAllocationSettingData.InstanceID="domgst/mem"
# 
# Using the above output we do the assocn for each of them on Xen_SettingsDefineState
# wbemcli ain -ac Xen_SettingsDefineState 'http://localhost:5988/root/virt:\
# Xen_ProcResourceAllocationSettingData.InstanceID="domgst/0"'
#
# Output:
# localhost:5988/root/virt:Xen_Processor.CreationClassName="Xen_Processor",             \
# DeviceID="domgst/0",SystemCreationClassName="",SystemName="domgst"
#
# Similarly verify the assoc on all the resources like Network, Disk and Memory.
#
# Date : 31-01-2008

import sys
from CimTest import Globals 
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from VirtLib import utils
from XenKvmLib import assoc
from XenKvmLib import vxml
from XenKvmLib.classes import get_typed_class, get_class_basename
from XenKvmLib.rasd import InstId_err

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom    = "virtgst"
test_vcpus  = 1
test_mem    = 128
test_mac    = "00:11:22:33:44:aa"

def call_assoc(ip, inst, exp_id, ccn, virt):
    if inst['InstanceID'] != exp_id:
        InstId_err(inst, exp_id)
        return FAIL

    try:
        associnf = assoc.Associators(ip, 'SettingsDefineState',
                                     ccn, virt,
                                     InstanceID = exp_id)
    except  BaseException, detail :
        logger.error("Exception  %s "  % detail)
        logger.error("Error while associating Xen_SettingsDefineState with %s" %
                     ccn)
        return FAIL

    return SettingsDefineStateAssoc(ip, associnf, virt)

def VSSDCAssoc(ip, assocn, virt):
    """
        The association info of Xen_VirtualSystemSettingDataComponent 
        is verified. 
    """

    status = PASS
    if len(assocn) == 0: 
        status = FAIL
        return status

    try: 
        for rasd in assocn:
            rasd_cn = get_class_basename(rasd.classname)
            if rasd_cn in rasd_devid.keys():
                status = call_assoc(ip, rasd, rasd_devid[rasd_cn], rasd_cn, virt)
            else:
                status = FAIL

            if status != PASS:
                logger.error("Mistmatching value for VSSDComponent association")
                break  

    except  BaseException, detail :
        logger.error("Exception in VSSDCAssoc function: %s" % detail)
        status = FAIL

    return status

def check_id(inst, exp_id):
    if inst['DeviceID'] != exp_id:
        return FAIL

    return PASS
   
def SettingsDefineStateAssoc(ip, associnfo_setDef, virt):
    """
        The association info of Xen_SettingsDefineState is verified. 
    """
    status = PASS
    
    if len(associnfo_setDef) == 0: 
        status = FAIL
        return status

    try: 
        for dev in associnfo_setDef:
            dev_cn = get_class_basename(dev['CreationClassName'])
            if dev_cn in dev_devid.keys():
                status = check_id(dev, dev_devid[dev_cn])
            else:
                status = FAIL

            if status != PASS:
                logger.error("Mistmatching value for SettingsDefineState assoc")
                break  

    except  BaseException, detail :
        logger.error("Exception in SettingsDefineStateAssoc function: %s" 
                     % detail)
        status = FAIL

    return status


@do_main(sup_types)
def main():
    options = main.options

    vt = options.virt
    if vt == 'Xen':
        test_disk = 'xvdb'
    else:
        test_disk = 'hdb'
    
    status = PASS 
    virt_xml = vxml.get_class(options.virt)
    if options.virt == 'LXC':
        cxml = virt_xml(test_dom)
    else:
        cxml = virt_xml(test_dom, mem = test_mem, vcpus = test_vcpus,
                        mac = test_mac, disk = test_disk)
    ret = cxml.create(options.ip)
    if not ret:
        logger.error("Failed to create the dom: %s", test_dom)
        status = FAIL
        return status


    if vt == 'XenFV':
        VSType = 'Xen'
    else:
        VSType = vt

    instIdval = "%s:%s" % (VSType, test_dom)

    vssdc_cn = get_typed_class(vt, 'VirtualSystemSettingDataComponent')
    vssd_cn = get_typed_class(vt, 'VirtualSystemSettingData')
    sds_cn = get_typed_class(vt, 'SettingsDefineState')

    global rasd_devid
    rasd_devid = {
            'ProcResourceAllocationSettingData' : '%s/%s' % (test_dom, 'proc'),
            'NetResourceAllocationSettingData'  : '%s/%s' % (test_dom, test_mac),
            'DiskResourceAllocationSettingData' : '%s/%s' % (test_dom, test_disk),
            'MemResourceAllocationSettingData'  : '%s/%s' % (test_dom, 'mem')}

    global dev_devid
    dev_devid = {
            'Processor'   : '%s/%s' % (test_dom, test_vcpus-1),
            'NetworkPort' : '%s/%s' % (test_dom, test_mac),
            'LogicalDisk' : '%s/%s' % (test_dom, test_disk),
            'Memory'      : '%s/%s' % (test_dom, 'mem')}

    try:
        assocn = assoc.AssociatorNames(options.ip, vssdc_cn, vssd_cn,
                                       virt = options.virt,
                                       InstanceID = instIdval)
            
        status = VSSDCAssoc(options.ip, assocn, options.virt)

    except  BaseException, detail :
        logger.error(Globals.CIM_ERROR_ASSOCIATORS, vssdc_cn)
        logger.error("Exception : %s" % detail)
        status = FAIL 

    cxml.destroy(options.ip)
    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())

