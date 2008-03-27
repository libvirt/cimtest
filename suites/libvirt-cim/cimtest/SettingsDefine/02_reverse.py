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
from CimTest.Globals import log_param, logger, do_main
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from VirtLib import utils
from XenKvmLib.test_xml import testxml
from XenKvmLib.test_doms import test_domain_function
from XenKvmLib import assoc
from XenKvmLib.rasd import InstId_err
from XenKvmLib.devices import Xen_NetworkPort, Xen_Memory, Xen_LogicalDisk, Xen_Processor


sup_types = ['Xen']

test_dom    = "virtgst"
test_vcpus  = 1
test_mem    = 128
test_mac    = "00:11:22:33:44:aa"
test_disk   = 'xvdb'
VSType      = "Xen"

resources = {
             "proc" : (test_dom + '/' + `0` ), \
             "net"  : (test_dom + '/' + test_mac), \
             "disk" : (test_dom + '/' + test_disk), \
             "mem"  : (test_dom + '/' + 'mem' )
           }

def call_assoc(ip, inst, exp_id, ccn):
    if inst['InstanceID'] != exp_id:
        InstId_err(inst, exp_id)
        return FAIL

    try:
        associnf = assoc.Associators(ip, 'Xen_SettingsDefineState', ccn, \
                                        InstanceID = exp_id)
    except  BaseException, detail :
        logger.error("Exception  %s "  % detail)
        logger.error("Error while associating Xen_SettingsDefineState with %s" %
                     ccn)
        return FAIL

    return SettingsDefineStateAssoc(ip, associnf)

def VSSDCAssoc(ip, assocn):
    """
        The association info of Xen_VirtualSystemSettingDataComponent 
        is verified. 
    """

    status = PASS
    if len(assocn) == 0: 
        status = FAIL
        return status

    try: 
        for i in range(len(assocn)): 
            if assocn[i].classname == 'Xen_ProcResourceAllocationSettingData':
                status = call_assoc(ip, assocn[i], resources['proc'],       \
                                    'Xen_ProcResourceAllocationSettingData')

            elif assocn[i].classname == 'Xen_NetResourceAllocationSettingData':
                status = call_assoc(ip, assocn[i], resources['net'],        \
                                    'Xen_NetResourceAllocationSettingData')

            elif assocn[i].classname =='Xen_DiskResourceAllocationSettingData':
                status = call_assoc(ip, assocn[i], resources['disk'],       \
                                     'Xen_DiskResourceAllocationSettingData')

            elif assocn[i].classname == 'Xen_MemResourceAllocationSettingData':
                status = call_assoc(ip, assocn[i], resources['mem'],        \
                                     'Xen_MemResourceAllocationSettingData')
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
   
def SettingsDefineStateAssoc(ip, associnfo_setDef):
    """
        The association info of Xen_SettingsDefineState is verified. 
    """
    status = PASS
    
    if len(associnfo_setDef) == 0: 
        status = FAIL
        return status

    try: 
        for i in range(len(associnfo_setDef)): 
        
            if associnfo_setDef[i]['CreationClassName'] == 'Xen_Processor':
                status = check_id(associnfo_setDef[i], resources['proc'])

            elif associnfo_setDef[i]['CreationClassName'] == 'Xen_NetworkPort':
                status = check_id(associnfo_setDef[i], resources['net'])

            elif associnfo_setDef[i]['CreationClassName'] == 'Xen_LogicalDisk':
                status = check_id(associnfo_setDef[i], resources['disk'])

            elif associnfo_setDef[i]['CreationClassName'] == 'Xen_Memory':
                status = check_id(associnfo_setDef[i], resources['mem'])

            else:
                status = FAIL

            if status != PASS:
                logger.error("Mistmatching value for SettingsDefineState assoc")
                break  

    except  BaseException, detail :
        logger.error("Exception in SettingsDefineStateAssoc function: %s" 
                     % detail)
        status = FAIL
        test_domain_function(test_dom, ip, "destroy")

    return status

@do_main(sup_types)
def main():
    options = main.options

    status = PASS 
    log_param()
    test_domain_function(test_dom, options.ip, "destroy")
    bld_xml = testxml(test_dom, mem = test_mem, vcpus = test_vcpus, 
                      mac = test_mac, disk = test_disk)

    ret = test_domain_function(bld_xml, options.ip, cmd = "create")
    if not ret:
        logger.error("Failed to create the dom: %s", test_dom)
        status = FAIL
        return status

    instIdval = "%s:%s" % (VSType, test_dom)

    try:
        assocn = assoc.AssociatorNames(options.ip, 
                                       'Xen_VirtualSystemSettingDataComponent',
                                       'Xen_VirtualSystemSettingData', 
                                       InstanceID = instIdval)
        status = VSSDCAssoc(options.ip, assocn)

    except  BaseException, detail :
        logger.error(Globals.CIM_ERROR_ASSOCIATORS, 
                        'Xen_VirtualSystemSettingDataComponent')
        logger.error("Exception : %s" % detail)
        status = FAIL 

    test_domain_function(test_dom, options.ip, "destroy")
    return status

if __name__ == "__main__":
    sys.exit(main())

