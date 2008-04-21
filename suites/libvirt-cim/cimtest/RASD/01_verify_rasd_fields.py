#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
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

# This test case is used to verify the ResourceAllocationSettingData
# properties in detail using the Xen_VirtualSystemSettingDataComponent
# association.
#
# Ex: 
# Command:
# wbemcli ai -ac Xen_VirtualSystemSettingDataComponent \
# 'http://localhost:5988/root/virt:Xen_VirtualSystemSettingData.\
#  InstanceID="Xen:domgst"'
#
# Output:
# localhost:5988/root/virt:Xen_ProcResourceAllocationSettingData.\
# InstanceID="domgst/0" .....
# localhost:5988/root/virt:Xen_NetResourceAllocationSettingData\
# .InstanceID="domgst/00:22:33:aa:bb:cc" ....
# localhost:5988/root/virt:Xen_DiskResourceAllocationSettingData.\
# InstanceID="domgst/xvda".....
# localhost:5988/root/virt:Xen_MemResourceAllocationSettingData.\
# InstanceID="domgst/mem".....
# 
# 
# 
# 
#                                               Date : 08-01-2008


import sys
from XenKvmLib import enumclass
from VirtLib import utils
from CimTest import Globals
from CimTest.Globals import do_main
from XenKvmLib.test_doms import destroy_and_undefine_all
import XenKvmLib
from XenKvmLib import assoc
from XenKvmLib import vxml 
from XenKvmLib.vxml import XenXML, KVMXML, get_class
from XenKvmLib.classes import get_typed_class
from XenKvmLib.rasd import verify_procrasd_values, verify_netrasd_values, \
verify_diskrasd_values, verify_memrasd_values 
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV']

test_dom    = "VSSDC_dom"
test_vcpus  = 1
test_mem    = 128
test_mac    = "00:11:22:33:44:aa"

def init_list(xml, disk, virt="Xen"):
    """
        Creating the lists that will be used for comparisons.
    """
    procrasd = {
                 "InstanceID" : '%s/%s' %(test_dom, "proc"),\
                 "ResourceType" : 3,\
                 "CreationClassName": get_typed_class(virt, 'ProcResourceAllocationSettingData')
                }

    netrasd = {
                "InstanceID"  : '%s/%s' %(test_dom,test_mac), \
                "ResourceType" : 10 , \
                "ntype1": "bridge", \
                "ntype2": "ethernet", \
                "CreationClassName": get_typed_class(virt, 'NetResourceAllocationSettingData')
               }

    address = xml.xml_get_disk_source()
    diskrasd = {
                "InstanceID"  : '%s/%s' %(test_dom, disk), \
                "ResourceType" : 17, \
                "Address"      : address, \
                "CreationClassName": get_typed_class(virt, 'DiskResourceAllocationSettingData')
               }
    memrasd = {
               "InstanceID"  : '%s/%s' %(test_dom, "mem"), \
               "ResourceType" : 4, \
               "AllocationUnits" : "KiloBytes",\
               "VirtualQuantity" : (test_mem * 1024), \
               "CreationClassName": get_typed_class(virt, 'MemResourceAllocationSettingData')
              }
    return procrasd, netrasd, diskrasd, memrasd

def assoc_values(ip, assoc_info, xml, disk, virt="Xen"):
    procrasd, netrasd, diskrasd, memrasd = init_list(xml, disk, virt)
    proc_status = 1
    net_status  = 0
    disk_status = 1
    mem_status  = 1
    status = 0
    try: 
        for i in range(len(assoc_info)): 
            if assoc_info[i]['InstanceID'] == procrasd['InstanceID']: 
                proc_status = verify_procrasd_values(assoc_info[i], procrasd)
            elif assoc_info[i]['InstanceID'] == netrasd['InstanceID']:
                net_status  = verify_netrasd_values(assoc_info[i], netrasd)
            elif assoc_info[i]['InstanceID'] == diskrasd['InstanceID']:
                disk_status = verify_diskrasd_values(assoc_info[i], diskrasd)
            elif assoc_info[i]['InstanceID'] == memrasd['InstanceID']:
                mem_status  = verify_memrasd_values(assoc_info[i], memrasd)
            else:
                status = 1
        if status != 0 or proc_status != 0 or net_status != 0 or \
           disk_status != 0 or mem_status != 0 :
            logger.error("Mistmatching association values" )
            status = 1 
    except  Exception, detail :
        logger.error("Exception in assoc_values function: %s" % detail)
        status = 1
    
    return status
   
@do_main(sup_types)
def main():
    options = main.options
    status = 0 
    rc = 1
    destroy_and_undefine_all(options.ip)
    if options.virt == 'Xen':
        test_disk = 'xvda'
    else:
        test_disk = 'hda'

    virt_xml = vxml.get_class(options.virt)
    cxml = virt_xml(test_dom, mem=test_mem, vcpus = test_vcpus, mac = test_mac, disk = test_disk)
    ret = cxml.create(options.ip)
    if not ret:
        logger.error('Unable to create domain %s' % test_dom)
        return FAIL 
    if status == 1: 
        destroy_and_undefine_all(options.ip)
        return 1
    if options.virt == "XenFV":
        instIdval = "Xen:%s" % test_dom
    else:
        instIdval = "%s:%s" % (options.virt, test_dom)
    
    try:
        assoc_info = assoc.Associators(options.ip, \
                                       'VirtualSystemSettingDataComponent', \
                                       'VirtualSystemSettingData', \
                                       options.virt, \
                                       InstanceID = instIdval)
        status = assoc_values(options.ip, assoc_info, cxml, test_disk, options.virt)
    except  Exception, details:
        logger.error(Globals.CIM_ERROR_ASSOCIATORS, \
                     get_typed_class(options.virt, 'VirtualSystemSettingDataComponent'))
        logger.error("Exception : %s" % details)
        status = 1 
    
    try:
        cxml.destroy(options.ip)
        cxml.undefine(options.ip)
    except Exception:
        logger.error("Destroy or undefine domain failed")
    return status

if __name__ == "__main__":
    sys.exit(main())
