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
from XenKvmLib.const import do_main
from XenKvmLib.test_doms import destroy_and_undefine_all
from XenKvmLib import assoc
from XenKvmLib import vxml 
from XenKvmLib.classes import get_typed_class
from XenKvmLib import rasd 
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib import rasd
from XenKvmLib.rasd import verify_procrasd_values, verify_netrasd_values, \
verify_diskrasd_values, verify_memrasd_values, rasd_init_list

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom    = "VSSDC_dom"
test_vcpus  = 1
test_mem    = 128
test_mac    = "00:11:22:33:44:aa"

def assoc_values(assoc_info, xml, disk, virt="Xen"):
    status, rasd_values, in_list = rasd_init_list(xml, virt, disk, test_dom,
                                                 test_mac, test_mem)
    if status != PASS:
        return status
    
    procrasd =  rasd_values['%s'  %in_list['proc']]
    netrasd  =  rasd_values['%s'  %in_list['net']] 
    diskrasd =  rasd_values['%s'  %in_list['disk']]
    memrasd  =  rasd_values['%s'  %in_list['mem']]

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
    virt = options.virt
    status = PASS 

    destroy_and_undefine_all(options.ip)
    if virt == 'Xen':
        test_disk = 'xvda'
    else:
        test_disk = 'hda'

    virt_xml = vxml.get_class(virt)
    if virt == 'LXC':
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
    if virt == "XenFV":
        instIdval = "Xen:%s" % test_dom
    else:
        instIdval = "%s:%s" % (virt, test_dom)

    vssdc_cn = get_typed_class(virt, 'VirtualSystemSettingDataComponent')
    vssd_cn = get_typed_class(virt, 'VirtualSystemSettingData')
    try:
        assoc_info = assoc.Associators(options.ip, vssdc_cn, vssd_cn, 
                                       InstanceID = instIdval)
        status = assoc_values(assoc_info, cxml, test_disk, virt)
    except  Exception, details:
        logger.error(Globals.CIM_ERROR_ASSOCIATORS, 
                     get_typed_class(virt, vssdc_cn))
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
