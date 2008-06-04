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
from CimTest import Globals
from CimTest.Globals import do_main
from XenKvmLib.test_doms import destroy_and_undefine_all
from XenKvmLib import assoc
from XenKvmLib import vxml 
from XenKvmLib.classes import get_typed_class
from XenKvmLib import rasd 
from XenKvmLib.const import CIM_REV
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom    = "VSSDC_dom"
test_vcpus  = 1
test_mem    = 128
test_mac    = "00:11:22:33:44:aa"
prev = 531
mrev = 529

def init_list(xml, disk, virt="Xen"):
    """
        Creating the lists that will be used for comparisons.
    """
    procrasd = {
            "InstanceID" : '%s/%s' % (test_dom, "proc"),
            "ResourceType" : 3,
            "CreationClassName" : get_typed_class(virt, rasd.pasd_cn)}
    netrasd = {
            "InstanceID" : '%s/%s' % (test_dom,test_mac),
            "ResourceType" : 10 ,
            "ntype1" : "bridge",
            "ntype2" : "ethernet",
            "CreationClassName" : get_typed_class(virt, rasd.nasd_cn)}
    address = xml.xml_get_disk_source()
    diskrasd = {
            "InstanceID" : '%s/%s' % (test_dom, disk),
            "ResourceType" : 17,
            "Address" : address,
            "CreationClassName" : get_typed_class(virt, rasd.dasd_cn)}
    memrasd = {
            "InstanceID" : '%s/%s' % (test_dom, "mem"),
            "ResourceType" : 4,
            "AllocationUnits" : "KiloBytes",
            "VirtualQuantity" : (test_mem * 1024),
            "CreationClassName" : get_typed_class(virt, rasd.masd_cn)}
    if CIM_REV < prev:
        procrasd['InstanceID'] = '%s/0' % test_dom
    if CIM_REV < mrev:
        memrasd['AllocationUnits'] = 'MegaBytes'

    return procrasd, netrasd, diskrasd, memrasd

def assoc_values(assoc_info, xml, disk, virt="Xen"):
    procrasd, netrasd, diskrasd, memrasd = init_list(xml, disk, virt)
    if virt == 'LXC':
        proc_status = 0
        disk_status = 0
    else:
        proc_status = 1
        disk_status = 1

    net_status  = 0
    mem_status  = 1
    status = 0
    try: 
        for res in assoc_info: 
            if res['InstanceID'] == procrasd['InstanceID']: 
                proc_status = rasd.verify_procrasd_values(res, procrasd)
            elif res['InstanceID'] == netrasd['InstanceID']:
                net_status  = rasd.verify_netrasd_values(res, netrasd)
            elif res['InstanceID'] == diskrasd['InstanceID']:
                disk_status = rasd.verify_diskrasd_values(res, diskrasd)
            elif res['InstanceID'] == memrasd['InstanceID']:
                mem_status  = rasd.verify_memrasd_values(res, memrasd)
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
    status = PASS 
    destroy_and_undefine_all(options.ip)
    if options.virt == 'Xen':
        test_disk = 'xvda'
    else:
        test_disk = 'hda'

    virt_xml = vxml.get_class(options.virt)
    if options.virt == 'LXC':
        cxml = virt_xml(test_dom)
    else:
        cxml = virt_xml(test_dom, mem=test_mem, vcpus = test_vcpus,
                        mac = test_mac, disk = test_disk)
    ret = cxml.create(options.ip)
    if not ret:
        logger.error('Unable to create domain %s' % test_dom)
        return FAIL 
    if status == 1: 
        destroy_and_undefine_all(options.ip)
        return FAIL
    if options.virt == "XenFV":
        instIdval = "Xen:%s" % test_dom
    else:
        instIdval = "%s:%s" % (options.virt, test_dom)

    vssdc_cn = 'VirtualSystemSettingDataComponent'
    vssd_cn = 'VirtualSystemSettingData'
    try:
        assoc_info = assoc.Associators(options.ip, vssdc_cn, vssd_cn, 
                                       options.virt,
                                       InstanceID = instIdval)
        status = assoc_values(assoc_info, cxml, test_disk, options.virt)
    except  Exception, details:
        logger.error(Globals.CIM_ERROR_ASSOCIATORS, 
                     get_typed_class(options.virt, vssdc_cn))
        logger.error("Exception : %s" % details)
        status = FAIL 
    
    try:
        cxml.destroy(options.ip)
        cxml.undefine(options.ip)
    except Exception:
        logger.error("Destroy or undefine domain failed")
    return status

if __name__ == "__main__":
    sys.exit(main())
