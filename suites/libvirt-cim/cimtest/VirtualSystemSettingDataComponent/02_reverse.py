#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
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

# This test case is used to verify the Xen_VirtualSystemSettingDataComponent
# association.
#
# Ex: Command and the fields that are verified are given below.
# wbemcli ain -ac Xen_VirtualSystemSettingDataComponent \
# 'http://localhost:5988/root/virt:Xen_VirtualSystemSettingData.\
#  InstanceID="Xen:domgst"'
#
# Output:
# localhost:5988/root/virt:Xen_ProcResourceAllocationSettingData.\
# InstanceID="domgst/0" 
# localhost:5988/root/virt:Xen_NetResourceAllocationSettingData\
# .InstanceID="domgst/00:22:33:aa:bb:cc" 
# localhost:5988/root/virt:Xen_DiskResourceAllocationSettingData.\
# InstanceID="domgst/xvda"
# localhost:5988/root/virt:Xen_MemResourceAllocationSettingData.\
# InstanceID="domgst/mem"
# 
# 
# 
#                                               Date : 01-01-2008


import sys
from XenKvmLib import enumclass
from VirtLib import utils
from XenKvmLib.test_doms import test_domain_function, destroy_and_undefine_all 
from XenKvmLib import test_xml
from XenKvmLib.test_xml import testxml
from CimTest import Globals 
from XenKvmLib import assoc
from XenKvmLib.rasd import InstId_err
from CimTest.Globals import log_param, logger, do_main
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen']

test_dom    = "VSSDC_dom"
test_vcpus  = 1
test_mem    = 128
test_mac    = "00:11:22:33:44:aa"
test_disk   = 'xvdb'
VSType      = "Xen"

def check_rasd_values(id, exp_id):
    try:
        if id != exp_id:
            InstId_err(assoc_info[i], rasd_list['proc_rasd'])
            return FAIL
 
    except Exception, detail :
        logger.error("Exception evaluating InstanceID: %s" % detail)
        return FAIL

    return PASS

def assoc_values(ip, assoc_info):
    """
        The association info of 
        Xen_VirtualSystemSettingDataComponent is
        verified. 
    """
    status = PASS
    rasd_list = {
                 "proc_rasd" : '%s/%s' %(test_dom,0), 
                 "net_rasd"  : '%s/%s' %(test_dom,test_mac),
                 "disk_rasd" : '%s/%s' %(test_dom, test_disk),
                 "mem_rasd"  : '%s/%s' %(test_dom, "mem")
                }
    try: 
        if len(assoc_info) <= 0: 
            logger.error("No RASD instances returned")
            return FAIL

        for inst in assoc_info: 
            if inst.classname == 'Xen_ProcResourceAllocationSettingData':
                status = check_rasd_values(inst['InstanceID'], 
                                           rasd_list['proc_rasd'])
            elif inst.classname == 'Xen_NetResourceAllocationSettingData':
                status = check_rasd_values(inst['InstanceID'], 
                                           rasd_list['net_rasd'])
            elif inst.classname == 'Xen_DiskResourceAllocationSettingData': 
                status = check_rasd_values(inst['InstanceID'], 
                                           rasd_list['disk_rasd'])
            elif inst.classname == 'Xen_MemResourceAllocationSettingData': 
                status = check_rasd_values(inst['InstanceID'], 
                                           rasd_list['mem_rasd'])
            else:
                logger.error("Unexpected RASD instance type" )
                status = FAIL

            if status != FAIL:
                logger.error("Mistmatching association value" )
                break  

    except  Exception, detail :
        logger.error("Exception in assoc_values function: %s" % detail)
        status = FAIL

    return status

@do_main(sup_types)
def main():
    options = main.options
    status = PASS
    log_param()

    destroy_and_undefine_all(options.ip)
    test_xml1 = testxml(test_dom, mem = test_mem, \
                               vcpus = test_vcpus, \
                                   mac = test_mac, \
                                    disk = test_disk)

    ret = test_domain_function(test_xml1, options.ip, cmd = "create")
    if not ret:
        logger.error("Failed to create the dom: %s", test_dom)
        status = FAIL
        return status


    instIdval = "%s:%s" % (VSType, test_dom)
    try:
        assoc_info = assoc.AssociatorNames(options.ip,
                                        'Xen_VirtualSystemSettingDataComponent',
                                        'Xen_VirtualSystemSettingData',
                                        InstanceID = instIdval)
        status = assoc_values(options.ip, assoc_info)
    except  Exception, detail :
        logger.error(Globals.CIM_ERROR_ASSOCIATORS, 
                     'Xen_VirtualSystemSettingDataComponent')
        logger.error("Exception : %s" % detail)
        status = FAIL

    test_domain_function(test_dom, options.ip, "destroy")
    return status

if __name__ == "__main__":
    sys.exit(main())
