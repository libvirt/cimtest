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

# This test case is used to verify the ResourceAllocationSettingData
# properties in detail.
#
#                                               Date : 26-03-2008
#


import sys
from XenKvmLib import enumclass
from CimTest.Globals import do_main, CIM_ERROR_ENUMERATE
from XenKvmLib.test_doms import destroy_and_undefine_all
from XenKvmLib.vxml import get_class
from XenKvmLib.classes import get_typed_class
from XenKvmLib import rasd 
from XenKvmLib.const import CIM_REV
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV']

test_dom    = "VSSDC_dom"
test_vcpus  = 1
test_mem    = 128
test_mac    = "00:11:22:33:44:aa"
prev = 531
mrev = 529

def init_list(virt):
    """
        Creating the lists that will be used for comparisons.
    """
    proc = {
            "InstanceID" : '%s/%s' % (test_dom, "proc"),
            "ResourceType" : 3,
            "CreationClassName" : get_typed_class(virt, rasd.pasd_cn)}
    net = {
            "InstanceID" : '%s/%s' % (test_dom,test_mac),
            "ResourceType" : 10 ,
            "ntype1" : "bridge",
            "ntype2" : "ethernet",
            "CreationClassName" : get_typed_class(virt, rasd.nasd_cn)}
    address = vsxml.xml_get_disk_source()
    disk = {
            "InstanceID"  : '%s/%s' % (test_dom, test_disk),
            "ResourceType" : 17,
            "Address" : address,
            "CreationClassName" : get_typed_class(virt, rasd.dasd_cn)}
    mem = {
            "InstanceID" : '%s/%s' % (test_dom, "mem"),
            "ResourceType" : 4,
            "AllocationUnits" : "KiloBytes",
            "VirtualQuantity" : (test_mem * 1024),
            "CreationClassName" : get_typed_class(virt, rasd.masd_cn)}
    if CIM_REV < prev:
        proc['InstanceID'] = '%s/0' % test_dom
    if CIM_REV < mrev:
        mem['AllocationUnits'] = 'MegaBytes'

    return proc, net, disk, mem

def get_inst_from_list(server, classname, rasd_list, filter_name, exp_val):
    status = PASS
    ret = FAIL 
    inst = []
    for rec in rasd_list:
        record = rec[filter_name['key']]
        if exp_val in record :
            inst.append(rec)
            ret = PASS
    if ret != PASS:
        logger.error("%s with %s was not returned" % (classname, exp_val))
        vsxml.undefine(server)
        status = FAIL
    return status, inst

def get_rasd_values(classname, virt, server):
    status = PASS
    rasd_list   = []
    try:
        rasd_list = enumclass.enumerate_inst(server, classname, virt)
        if len(rasd_list) < 1:
            logger.error("%s returned %i instances, excepted at least 1.",
                    classname, len(rasd_list))
            return FAIL, rasd_list
    except Exception, detail:
        logger.error(CIM_ERROR_ENUMERATE, classname)
        logger.error("Exception: %s", detail)
        return FAIL, rasd_list

    # Get the RASD info related to the domain "ONLY". 
    # We should get atleast one record.
    filter_name =  {"key" : "InstanceID"}
    status, rasd_values = get_inst_from_list(server, classname, rasd_list,
                                             filter_name, test_dom)
    if status != PASS or len(rasd_values) == 0:
        return status, rasd_values

    return status, rasd_values 
            

def verify_rasd_values(rasd_values_info):
    try: 
        for rasd_instance in rasd_values_info:
            CCName = rasd_instance.classname
            if rasd.pasd_cn in CCName :
                status = rasd.verify_procrasd_values(rasd_instance, procrasd,)
            elif rasd.nasd_cn in CCName :
                status = rasd.verify_netrasd_values(rasd_instance, netrasd)
            elif rasd.dasd_cn in CCName:
                status = rasd.verify_diskrasd_values(rasd_instance, diskrasd)
            elif rasd.masd_cn in CCName :
                status = rasd.verify_memrasd_values(rasd_instance, memrasd)
            else:
                status = FAIL
            if status != PASS:
                logger.error("Mistmatching %s values", CCName )
                break
    except  Exception, detail :
        logger.error("Exception in verify_rasd_values function: %s" % detail)
        status =  FAIL
    return status
   
@do_main(sup_types)
def main():
    virt = main.options.virt
    server = main.options.ip
    destroy_and_undefine_all(server)
    global test_disk, vsxml
    global procrasd, netrasd, diskrasd, memrasd
    if virt == "Xen":
        test_disk = "xvda"
    else:
        test_disk = "hda"
    virtxml = get_class(virt)
    vsxml = virtxml(test_dom, mem=test_mem, vcpus = test_vcpus,
                    mac = test_mac, disk = test_disk)
    try:
        vsxml.set_vbridge(server)
        ret = vsxml.define(server)
        if not ret:
            logger.error("Failed to Define the domain: %s", test_dom)
            return FAIL 
    except Exception, details:
        logger.error("Exception : %s", details)
        return FAIL
    class_list = [ get_typed_class(virt, rasd.dasd_cn), 
                   get_typed_class(virt, rasd.masd_cn), 
                   get_typed_class(virt, rasd.pasd_cn), 
                   get_typed_class(virt, rasd.nasd_cn)
                 ]  
    status = PASS 
    procrasd, netrasd, diskrasd, memrasd = init_list(virt)
    
    # For each loop
    # 1) Enumerate one RASD type
    # 2) Get the RASD info related to the domain "ONLY".
    # 3) Verifies the RASD values with those supplied during
    #    defining the domain.

    for classname in sorted(class_list):
        # Enumerate each RASD types
        status, rasd_values = get_rasd_values(classname, virt, server)
        if status != PASS or len(rasd_values) ==0 :
            break

        # Verify RASD values. 
        status = verify_rasd_values(rasd_values)
        if status != PASS:
            break

    try: 
        vsxml.undefine(server)
    except Exception, detail:
        logger.error("Failed to undefine domain %s", test_dom)
        logger.error("Exception: %s", detail)
        status = FAIL
    return status 

if __name__ == "__main__":
    sys.exit(main())
