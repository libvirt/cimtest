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
# Ex: Commanad and the fields that are verified are given below.
# wbemcli ai -ac Xen_VirtualSystemSettingDataComponent 
# 'http://localhost:5988/root/virt:
#
# Output:
# Xen_MemResourceAllocationSettingData.InstanceID="domgst/mem"'
# 
# Fields verified for association Xen_VirtualSystemSettingDataComponent 
# with Xen_MemResourceAllocationSettingData
#
#-Caption="Virtual System"
#-InstanceID="Xen:Domain"
#-ElementName="Domain"
#-VirtualSystemIdentifier="Domain"
#-VirtualSystemType="Xen"
#-Bootloader="/usr/bin/pygrub"
# 
# Similary we verify Xen_VirtualSystemSettingDataComponent association with 
# Xen_NetResourceAllocationSettingData
# Xen_DiskResourceAllocationSettingData and 
# Xen_ProcResourceAllocationSettingData classes.
# 
#                                               Date : 12-12-2007


import sys
from XenKvmLib import enumclass
from VirtLib import utils
from XenKvmLib.test_doms import destroy_and_undefine_all
from XenKvmLib.assoc import compare_all_prop 
from CimTest import Globals 
from XenKvmLib import assoc
from XenKvmLib import vxml
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger
from XenKvmLib.const import do_main, get_provider_version
from CimTest.ReturnCodes import FAIL, PASS

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
input_graphics_pool_rev = 757

test_dom    = "VSSDC_dom"
test_vcpus  = 2
test_mac    = "00:11:22:33:44:aa"

def init_list(test_disk, test_mac, server, virt='Xen'):
    """
        Creating the lists that will be used for comparisons.
    """

    rlist = [get_typed_class(virt, 'DiskResourceAllocationSettingData'),
             get_typed_class(virt, 'MemResourceAllocationSettingData'),
             get_typed_class(virt, 'NetResourceAllocationSettingData'),
             get_typed_class(virt, 'ProcResourceAllocationSettingData')
            ]

    prop_list = {rlist[0] : "%s/%s"  % (test_dom, test_disk),
                 rlist[1] : "%s/%s" % (test_dom, "mem"),
                 rlist[2] : "%s/%s" % (test_dom, test_mac),
                 rlist[3] : "%s/%s" % (test_dom, "proc")
                }

    if virt == 'LXC':
        input_device = "mouse:usb"
    elif virt == 'Xen':
        input_device = "mouse:xen"
    else:
        input_device = "mouse:ps2"
        
    curr_cim_rev, changeset = get_provider_version(virt, server)
    if curr_cim_rev >= input_graphics_pool_rev:
        input = get_typed_class(virt,'InputResourceAllocationSettingData')
        graphics = get_typed_class(virt,'GraphicsResourceAllocationSettingData')
        rlist.append(input)
        rlist.append(graphics)
        prop_list[input] = "%s/%s" % (test_dom, input_device)
        prop_list[graphics] = "%s/%s" % (test_dom, "graphics")

    if virt == 'LXC':
        prop_list = {rlist[1] : "%s/%s" % (test_dom, "mem")}        

    return prop_list

def assoc_values(ip, assoc_info, cn, an, vssd):
    """
        The association info of 
        Xen_VirtualSystemSettingDataComponent with every RASDclass is
        verified all of the values
    """

    try: 
        if len(assoc_info) != 1:
            logger.error("%s returned %i resource objects for '%s'",
                         an, len(assoc_info), cn)
            return FAIL 
        status = compare_all_prop(assoc_info[0], vssd)
        if status != PASS:
            logger.error("Properties of inst returned by %s didn't \
                         match expected", assoc_info[0].classname)
            return FAIL
    except  Exception, detail :
        logger.error("Exception in assoc_values function: %s", detail)
        return FAIL

    return PASS 

@do_main(sup_types)
def main():
    options = main.options
    status = FAIL

    destroy_and_undefine_all(options.ip)

    if options.virt == "Xen":
        test_disk = "xvdb"
    else:
        test_disk = "hdb"

    prop_list = init_list(test_disk, test_mac, options.ip, options.virt)
    virt_xml = vxml.get_class(options.virt)
    if options.virt == 'LXC':
        cxml = virt_xml(test_dom)
    else:
        cxml = virt_xml(test_dom, vcpus = test_vcpus, \
                        mac = test_mac, disk = test_disk)
    ret = cxml.cim_define(options.ip)
    if not ret:
        logger.error("Failed to define the dom: %s", test_dom)
        return FAIL 

    if options.virt == 'XenFV':
        instIdval = "Xen:%s" % test_dom
    else:
        instIdval = "%s:%s" % (options.virt, test_dom)

    keyname = "InstanceID"
    key_list = { 'InstanceID' : instIdval }
    vssd_cn = get_typed_class(options.virt, 'VirtualSystemSettingData')

    try:
        vssd = enumclass.GetInstance(options.ip, vssd_cn, key_list)
        if vssd is None:
            logger.error("VSSD instance for %s not found", test_dom)
            cxml.undefine(options.ip)
            return FAIL
    except  Exception, detail :
        logger.error(Globals.CIM_ERROR_GETINSTANCE, vssd_cn)
        logger.error("Exception : %s", detail)
        cxml.undefine(options.ip)
        return FAIL 


    try:
        # Looping through the RASD_cllist, call association 
        # Xen_VirtualSystemSettingDataComponent with each class in RASD_cllist
        an = get_typed_class(options.virt, 'VirtualSystemSettingDataComponent')
        for rasd_cname, prop in prop_list.iteritems():
            assoc_info = assoc.Associators(options.ip, an, rasd_cname,
                                           InstanceID = prop)
            # Verify the association fields returned for particular rasd_cname.
            status = assoc_values(options.ip, assoc_info, rasd_cname, an, 
                                  vssd)
            if status != PASS:
                break
 
    except  Exception, detail :
        logger.error(Globals.CIM_ERROR_ASSOCIATORS, an)
        logger.error("Exception : %s", detail)
        status = FAIL

    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())
