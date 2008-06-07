#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <deeptik@linux.vnet.ibm.com>
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
# This is a cross-provider testcase to 
# Get the setting data properties for the given guest.
#
#
# It traverses the following path: 
# {VSSD} --> [VirtualSystemSettingDataComponent](RASD)
# (Verify the Device RASD returned with the values expected - those given in test_xml)
#
# Steps:
# ------
# 1) Define a guest domain.
# 1) Get the VSSD info using enumeration. 
# 2) From the VSSD output get the info related to the domain. We expect only one
#    VSSD info related to the domain to be returned.
# 4) Get the various devices allocated to the domain by using the VirtualSystemSettingDataComponent
#    association and giving the VSSD output from the previous VSSD enumeration as inputs. 
# 5) Verify the Disk, Memory, Network, Processor RASD values.
# 7) Undefine the guest domain.
# 
#                                               Date : 26-03-2008


import sys
import XenKvmLib
from XenKvmLib import enumclass
from CimTest.Globals import do_main, CIM_ERROR_ASSOCIATORS, CIM_ERROR_ENUMERATE
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.test_doms import destroy_and_undefine_all
from XenKvmLib import assoc
from XenKvmLib.vxml import get_class
from XenKvmLib.classes import get_typed_class
from XenKvmLib.rasd import verify_procrasd_values, verify_netrasd_values, \
verify_diskrasd_values, verify_memrasd_values 
from XenKvmLib.const import CIM_REV

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom    = "VSSDC_dom"
test_vcpus  = 1
test_mem    = 128
test_mac    = "00:11:22:33:44:aa"
proc_rev = 531
mem_rev = 529

def setup_env(virt):  
    vsxml_info = None
    virt_xml = get_class(virt)
    if virt == 'LXC':
        vsxml_info = virt_xml(test_dom)
    else:
        vsxml_info = virt_xml(test_dom,  mem=test_mem, vcpus = test_vcpus,
                              mac = test_mac, disk = test_disk)
        try:
            bridge = vsxml_info.set_vbridge(server)
        except Exception, details:
            logger.error("Exception : %s", details)
            return FAIL, vsxml_info

    try:
        ret = vsxml_info.define(server)
        if not ret:
            logger.error("Failed to Define the domain: %s", test_dom)
            return FAIL, vsxml_info
    except Exception, details:
        logger.error("Exception : %s", details)
        return FAIL, vsxml_info
    return PASS, vsxml_info

def init_list(virt):
    """
        Creating the lists that will be used for comparisons.
    """
    procrasd = {
                 "InstanceID" : '%s/%s' %(test_dom, "proc"),
                 "ResourceType" : 3,
                 "CreationClassName": get_typed_class(virt, 'ProcResourceAllocationSettingData')
                }
    if CIM_REV < proc_rev:
        procrasd['InstanceID'] = '%s/%s' %(test_dom, "0")

    netrasd = {
                "InstanceID"  : '%s/%s' %(test_dom,test_mac), 
                "ResourceType" : 10 , 
                "ntype1": "bridge", 
                "ntype2": "ethernet", 
                "CreationClassName": get_typed_class(virt, 'NetResourceAllocationSettingData')
               }

    address = vsxml.xml_get_disk_source()
    diskrasd = {
                "InstanceID"  : '%s/%s' %(test_dom, test_disk), 
                "ResourceType" : 17, 
                "Address"      : address, 
                "CreationClassName": get_typed_class(virt, 'DiskResourceAllocationSettingData')
               }
    memrasd = {
               "InstanceID"  : '%s/%s' %(test_dom, "mem"), 
               "ResourceType" : 4, 
               "AllocationUnits" : "KiloBytes",
               "VirtualQuantity" : (test_mem * 1024), 
               "CreationClassName": get_typed_class(virt, 'MemResourceAllocationSettingData')
              }
    if CIM_REV < mem_rev:
        memrasd['AllocationUnits'] = "MegaBytes"
    return procrasd, netrasd, diskrasd, memrasd

def get_inst_from_list(classname, vssd_list, filter_name, exp_val):
    status = PASS
    ret = -1
    inst = []
    for rec in vssd_list:
        record = rec[filter_name['key']]
        if record.find(exp_val) >=0 :
            inst.append(rec)
            ret = PASS

    # When no records are found.
    if ret != PASS:
        logger.error("%s with %s was not returned" % (classname, exp_val))
        status = FAIL

    # We expect only one record to be returned. 
    if len(inst) != 1:
        logger.error("%s returned %i %s objects, expected only 1" % (classname, len(inst), 'VSSD'))
        status = FAIL

    if status != PASS: 
        vsxml.undefine(server)

    return status, inst

def get_vssd_info():
    vssd = []
    status = PASS
    try:
        classname   =  get_typed_class(virt, 'VirtualSystemSettingData')
        vssd = enumclass.enumerate_inst(server, eval('enumclass.' + classname), virt)
        if len(vssd) < 1 :
            logger.error("%s returned %i %s objects, expected atleast 1" % (classname, len(vssd), 'VSSD'))
            status = FAIL

    except Exception, detail:
        logger.error(CIM_ERROR_ENUMERATE, classname)
        logger.error("Exception: %s", detail)
        status = FAIL

    if status != PASS:
        return status, vssd

    filter_name =  {"key" : "InstanceID"}
    # Get the info ONLY related to the domain.
    status, vssd_values  = get_inst_from_list(classname, vssd, filter_name, test_dom)

    return status, vssd_values

def get_rasd_values_from_vssdc_assoc(vssd_values):   
    status = PASS
    vssdc_assoc_info = []
    # We should have only one VSSD record, the check for this is already done in 
    # get_inst_from_list() function, hence can safely use index 0.
    instIdval = vssd_values[0]['InstanceID']
    qcn       = vssd_values[0].classname
    assoc_cname = get_typed_class(virt, 'VirtualSystemSettingDataComponent')
    try:
        vssdc_assoc_info = assoc.Associators(server, assoc_cname, qcn, virt, InstanceID = instIdval)
        if len(vssdc_assoc_info) == 1 and \
           vssdc_assoc_info[0].classname == 'LXC_MemResourceAllocationSettingData':
           logger.info("%s returned expect objects" % assoc_cname)
        elif len(vssdc_assoc_info) < 4:
            logger.error("%s returned %i %s objects, expected 4" % (assoc_cname, len(vssdc_assoc_info), qcn))
            status = FAIL
            
    except  Exception, details:
        logger.error(CIM_ERROR_ASSOCIATORS, assoc_cname)
        logger.error("Exception : %s" % details)
        status = FAIL 
    return status, vssdc_assoc_info

def verify_rasd_values(rasd_values_info):
    procrasd, netrasd, diskrasd, memrasd = init_list(virt)
    try:
        for rasd_instance in rasd_values_info:
            CCName = rasd_instance.classname
            if  'ProcResourceAllocationSettingData' in CCName:
                status = verify_procrasd_values(rasd_instance, procrasd)
            elif 'NetResourceAllocationSettingData' in CCName :
                status  = verify_netrasd_values(rasd_instance, netrasd)
            elif 'DiskResourceAllocationSettingData' in CCName:
                status = verify_diskrasd_values(rasd_instance, diskrasd)
            elif 'MemResourceAllocationSettingData' in CCName :
                status  = verify_memrasd_values(rasd_instance, memrasd)
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
    options = main.options
    destroy_and_undefine_all(options.ip)
    global test_disk, vsxml
    global virt, server
    server = options.ip
    virt = options.virt
    if virt == "Xen":
        test_disk = "xvda"
    else:
        test_disk = "hda"

    status, vsxml = setup_env(virt)
    if status != PASS:
        return status

    status, vssd_values = get_vssd_info()
    if status != PASS or len(vssd_values) == 0:
        return status

    status, rasd_values = get_rasd_values_from_vssdc_assoc(vssd_values) 
    if status != PASS or len(rasd_values) == 0:
        vsxml.undefine(server)
        return status

    status = verify_rasd_values(rasd_values)
    try: 
        vsxml.undefine(server)
    except Exception, detail:
        logger.error("Failed to undefine domain %s", test_dom)
        logger.error("Exception: %s", detail)
        status = FAIL
    return status 

if __name__ == "__main__":
    sys.exit(main())
