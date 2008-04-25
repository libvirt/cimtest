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
from CimTest import Globals 
from XenKvmLib import assoc
from XenKvmLib.test_doms import destroy_and_undefine_all 
from XenKvmLib import vxml
from XenKvmLib.classes import get_typed_class
from XenKvmLib.rasd import InstId_err
from CimTest.Globals import logger, do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.const import CIM_REV

sup_types = ['Xen', 'XenFV', 'KVM']

test_dom    = "VSSDC_dom"
test_vcpus  = 1
test_mem    = 128
test_mac    = "00:11:22:33:44:aa"
rev = 531

def check_rasd_values(id, exp_id):
    try:
        if id != exp_id:
            InstId_err(assoc_info[i], rasd_list['proc_rasd'])
            return FAIL
 
    except Exception, detail :
        logger.error("Exception evaluating InstanceID: %s" % detail)
        return FAIL

    return PASS

def assoc_values(ip, assoc_info, virt="Xen"):
    """
        The association info of 
        Xen_VirtualSystemSettingDataComponent is
        verified. 
    """
    status = PASS
    rasd_list = {
                 "proc_rasd" : '%s/%s' %(test_dom, "proc"), 
                 "net_rasd"  : '%s/%s' %(test_dom,test_mac),
                 "disk_rasd" : '%s/%s' %(test_dom, test_disk),
                 "mem_rasd"  : '%s/%s' %(test_dom, "mem")
                }
    if CIM_REV < rev:
        rasd_list['proc_rasd'] = '%s/%s' %(test_dom, "0")

    try: 
        if len(assoc_info) <= 0: 
            logger.error("No RASD instances returned")
            return FAIL

        proc_cn = get_typed_class(virt, 'ProcResourceAllocationSettingData')
        net_cn = get_typed_class(virt, 'NetResourceAllocationSettingData')
        disk_cn = get_typed_class(virt, 'DiskResourceAllocationSettingData')
        mem_cn = get_typed_class(virt, 'MemResourceAllocationSettingData')
    
        for inst in assoc_info: 
            if inst.classname == proc_cn:
                status = check_rasd_values(inst['InstanceID'], 
                                           rasd_list['proc_rasd'])
            elif inst.classname == net_cn:
                status = check_rasd_values(inst['InstanceID'], 
                                           rasd_list['net_rasd'])
            elif inst.classname == disk_cn: 
                status = check_rasd_values(inst['InstanceID'], 
                                           rasd_list['disk_rasd'])
            elif inst.classname == mem_cn: 
                status = check_rasd_values(inst['InstanceID'], 
                                           rasd_list['mem_rasd'])
            else:
                logger.error("Unexpected RASD instance type" )
                status = FAIL

            if status == FAIL:
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

    destroy_and_undefine_all(options.ip)

    global test_disk
    if options.virt == "Xen":
        test_disk = "xvdb"
    else:
        test_disk = "hdb"
    virt_xml = vxml.get_class(options.virt)
    cxml = virt_xml(test_dom, vcpus = test_vcpus, mac = test_mac, disk = test_disk)
    ret = cxml.create(options.ip)
    if not ret:
        logger.error("Failed to create the dom: %s", test_dom)
        status = FAIL
        return status

    if options.virt == "Xen" or options.virt == "XenFV":
        instIdval = "Xen:%s" % test_dom
    else:
        instIdval = "KVM:%s" % test_dom
    
    try:
        assoc_info = assoc.AssociatorNames(options.ip,
                                           'VirtualSystemSettingDataComponent',
                                           'VirtualSystemSettingData',
                                           options.virt,
                                           InstanceID = instIdval)
        status = assoc_values(options.ip, assoc_info, options.virt)
    except  Exception, detail :
        logger.error(Globals.CIM_ERROR_ASSOCIATORS, 
                     'VirtualSystemSettingDataComponent')
        logger.error("Exception : %s" % detail)
        status = FAIL

    cxml.destroy(options.ip)
    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())
