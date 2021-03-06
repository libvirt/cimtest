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
from CimTest.Globals import logger, CIM_ERROR_ASSOCIATORS, CIM_ERROR_ENUMERATE
from XenKvmLib.const import do_main 
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC
from XenKvmLib.test_doms import destroy_and_undefine_all
from XenKvmLib import assoc
from XenKvmLib.vxml import get_class
from XenKvmLib.classes import get_typed_class
from XenKvmLib.xm_virt_util import virsh_version, virsh_version_cmp
from XenKvmLib import rasd
from XenKvmLib.rasd import verify_procrasd_values, verify_netrasd_values, \
verify_diskrasd_values, verify_memrasd_values, verify_displayrasd_values, \
rasd_init_list, verify_inputrasd_values, verify_controllerrasd_values
from XenKvmLib.const import default_network_name 

libvirt_bug = "00009"
sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom    = "VSSDC_dom"
test_vcpus  = 1
test_mem    = 128
test_mac    = "00:11:22:33:44:aa"

def setup_env(virt):  
    vsxml_info = None
    virt_xml = get_class(virt)
    if virt == 'LXC':
        vsxml_info = virt_xml(test_dom)
    else:
        vsxml_info = virt_xml(test_dom,  mem=test_mem, vcpus = test_vcpus,
                              mac = test_mac, disk = test_disk)

    try:
        ret = vsxml_info.cim_define(server)
        if not ret:
            logger.error("Failed to Define the domain: %s", test_dom)
            return FAIL, vsxml_info
    except Exception, details:
        logger.error("Exception : %s", details)
        return FAIL, vsxml_info
    return PASS, vsxml_info

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
        logger.error("%s with %s was not returned", classname, exp_val)
        status = FAIL

    # We expect only one record to be returned. 
    if len(inst) != 1:
        logger.error("%s returned %i %s objects, expected only 1", classname,
                     len(inst), 'VSSD')
        status = FAIL

    if status != PASS: 
        vsxml.undefine(server)

    return status, inst

def get_vssd_info():
    vssd = []
    status = PASS
    try:
        classname   =  get_typed_class(virt, 'VirtualSystemSettingData')
        vssd = enumclass.EnumNames(server, classname)
        if len(vssd) < 1 :
            logger.error("%s returned %i %s objects, expected atleast 1",
                          classname, len(vssd), 'VSSD')
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
        vssdc_assoc_info = assoc.Associators(server, assoc_cname, qcn, 
                                             InstanceID = instIdval)
        if len(vssdc_assoc_info) == 1 and \
           vssdc_assoc_info[0].classname == 'LXC_MemResourceAllocationSettingData':
           logger.info("%s returned expect objects", assoc_cname)
        elif len(vssdc_assoc_info) < 4:
            logger.error("%s returned %i %s objects, expected 4", 
                         assoc_cname, len(vssdc_assoc_info), qcn)
            status = FAIL
            
    except  Exception, details:
        logger.error(CIM_ERROR_ASSOCIATORS, assoc_cname)
        logger.error("Exception : %s", details)
        status = FAIL 
    return status, vssdc_assoc_info

def verify_rasd_values(rasd_values_info, server):
    status, rasd_values_list, in_list = rasd_init_list(vsxml, virt, test_disk,
                                                       test_dom, test_mac,
                                                       test_mem, server)
    if status != PASS:
        return status

    procrasd =  rasd_values_list['%s'  %in_list['proc']]
    netrasd  =  rasd_values_list['%s'  %in_list['net']]
    diskrasd =  rasd_values_list['%s'  %in_list['disk']]
    memrasd  =  rasd_values_list['%s'  %in_list['mem']]
    displayrasd = rasd_values_list['%s' %in_list['display']]
    controllerrasd = rasd_values_list['%s' %in_list['controller']]
    inputrasd = rasd_values_list['%s' %in_list['point']]

    # libvirt 1.2.2 adds a keyboard as an input option for KVM domains
    # so we need to handle that
    has_keybd = False
    if virt == 'KVM':
        libvirt_version = virsh_version(server, virt)
        if virsh_version_cmp(libvirt_version, "1.2.2") >= 0:
            keybdrasd = rasd_values_list['%s' %in_list['keyboard']]
            has_keybd = True

    try:
        for rasd_instance in rasd_values_info:
            CCName = rasd_instance.classname
            InstanceID = rasd_instance['InstanceID']
            if  'ProcResourceAllocationSettingData' in CCName:
                status = verify_procrasd_values(rasd_instance, procrasd)
            elif 'NetResourceAllocationSettingData' in CCName :
                status  = verify_netrasd_values(rasd_instance, netrasd)
            elif 'DiskResourceAllocationSettingData' in CCName:
                status = verify_diskrasd_values(rasd_instance, diskrasd)
            elif 'MemResourceAllocationSettingData' in CCName :
                status  = verify_memrasd_values(rasd_instance, memrasd)
            elif 'GraphicsResourceAllocationSettingData' in CCName :
                status = verify_displayrasd_values(rasd_instance, displayrasd)
            elif 'ControllerResourceAllocationSettingData' in CCName :
                status = verify_controllerrasd_values(rasd_instance,
                                                      controllerrasd)
            elif 'InputResourceAllocationSettingData' in CCName and \
                 virt == 'KVM' and 'keyboard' in InstanceID :
                # Force the issue - dictionary is keyed this way if
                # there is a keyboard device supported
                status = verify_displayrasd_values(rasd_instance, keybdrasd)
            elif 'InputResourceAllocationSettingData' in CCName and \
                 'keyboard' not in InstanceID:
                status = verify_inputrasd_values(rasd_instance, inputrasd)
                if status != PASS and virt== 'LXC':
                    return XFAIL_RC(libvirt_bug)
            else:
                status = FAIL
            if status != PASS:
                logger.error("Mismatching %s values", CCName )
                break
    except  Exception, detail :
        logger.error("Exception in verify_rasd_values function: %s", detail)
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
    if virt == "LXC":
        test_disk = "/tmp"
    else:
        test_disk = "vda"

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

    status = verify_rasd_values(rasd_values, server)
    try: 
        vsxml.undefine(server)
    except Exception, detail:
        logger.error("Failed to undefine domain %s", test_dom)
        logger.error("Exception: %s", detail)
        status = FAIL
    return status 

if __name__ == "__main__":
    sys.exit(main())
