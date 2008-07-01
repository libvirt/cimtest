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
from XenKvmLib.test_doms import test_domain_function, destroy_and_undefine_all 
from XenKvmLib.test_xml import testxml_bl
from XenKvmLib.test_xml import xml_get_dom_bootloader 
from CimTest import Globals 
from XenKvmLib import assoc
from CimTest.Globals import logger, do_main
from CimTest.ReturnCodes import FAIL, PASS

sup_types = ['Xen']

test_dom    = "VSSDC_dom"
test_vcpus  = 2
test_mac    = "00:11:22:33:44:aa"
test_disk   = 'xvda'
status      = 0
VSType      = "Xen"

def init_list():
    """
        Creating the lists that will be used for comparisons.
    """

    rlist = ['Xen_DiskResourceAllocationSettingData',
             'Xen_MemResourceAllocationSettingData',
             'Xen_NetResourceAllocationSettingData',
             'Xen_ProcResourceAllocationSettingData'
            ]

    prop_list = {rlist[0] : "%s/%s"  % (test_dom, test_disk),
                 rlist[1] : "%s/%s" % (test_dom, "mem"),
                 rlist[2] : "%s/%s" % (test_dom, test_mac),
                 rlist[3] : "%s/%s" % (test_dom, "proc")
                }

    return prop_list

def build_vssd_info(ip, vssd):
    """
        Creating the vssd fileds lists that will be used for comparisons.
    """

    if vssd.Bootloader == "" or vssd.Caption == "" or \
      vssd.InstanceID == "" or vssd.ElementName == "" or \
      vssd.VirtualSystemIdentifier == "" or vssd.VirtualSystemType == "":
        logger.error("One of the required VSSD details seems to be empty")
        test_domain_function(test_dom, ip, "undefine")
        return FAIL
 
    vssd_vals = {'Bootloader'			: vssd.Bootloader,
                 'Caption'			: vssd.Caption,
                 'InstanceID'			: vssd.InstanceID,
                 'ElementName'			: vssd.ElementName,
                 'VirtualSystemIdentifier'	: vssd.VirtualSystemIdentifier,
                 'VirtualSystemType'		: vssd.VirtualSystemType
                }

    return vssd_vals

def assoc_values(ip, assoc_info, cn, an, vals):
    """
        The association info of 
        Xen_VirtualSystemSettingDataComponent with every RASDclass is
        verified for following fields:
        Caption, InstanceID, ElementName, VirtualSystemIdentifier,
        VirtualSystemType, Bootloader
    """

    try: 
        if len(assoc_info) != 1:
            Globals.logger.error("%s returned %i resource objects for '%s'" % \
                                 (an, len(assoc_info), cn))
            return FAIL 

        for prop, val in vals.iteritems():
            if assoc_info[0][prop] != val:
                Globals.logger.error("%s mismatch: returned %s instead of %s" %\
                                     (prop, assoc_info[0][prop], val))
                return FAIL

        return PASS

    except  Exception, detail :
        logger.error("Exception in assoc_values function: %s" % detail)
        return FAIL 

@do_main(sup_types)
def main():
    options = main.options
    status = FAIL

    destroy_and_undefine_all(options.ip)
    test_xml = testxml_bl(test_dom, vcpus = test_vcpus, \
                          mac = test_mac, disk = test_disk, \
                          server = options.ip,\
                          gtype = 0)
    ret = test_domain_function(test_xml, options.ip, cmd = "define")
    if not ret:
        logger.error("Failed to define the dom: %s", test_dom)
        return FAIL 

    instIdval = "%s:%s" % (VSType, test_dom)
    keyname = "InstanceID"

    key_list = { 'InstanceID' : instIdval }
    try:
        vssd = enumclass.getInstance(options.ip, \
                                    enumclass.Xen_VirtualSystemSettingData, \
                                    key_list)
        if vssd is None:
            logger.error("VSSD instance for %s not found" % test_dom)
            test_domain_function(test_dom, options.ip, "undefine")
            return FAIL

        vssd_vals = build_vssd_info(options.ip, vssd)

    except  Exception, detail :
        logger.error(Globals.CIM_ERROR_GETINSTANCE, \
                     'Xen_VirtualSystemSettingData')
        logger.error("Exception : %s" % detail)
        test_domain_function(test_dom, options.ip, "undefine")
        return FAIL 

    prop_list = init_list()

    try:
        # Looping through the RASD_cllist, call association 
        # Xen_VirtualSystemSettingDataComponent with each class in RASD_cllist
        an = 'Xen_VirtualSystemSettingDataComponent'
        for rasd_cname, prop in prop_list.iteritems():
            assoc_info = assoc.Associators(options.ip, an, rasd_cname,
                                           InstanceID = prop)
            # Verify the association fields returned for particular rasd_cname.
            status = assoc_values(options.ip, assoc_info, rasd_cname, an, 
                                  vssd_vals)
            if status != PASS:
                break
 
    except  Exception, detail :
        logger.error(Globals.CIM_ERROR_ASSOCIATORS, an)
        logger.error("Exception : %s" % detail)
        status = FAIL

    test_domain_function(test_dom, options.ip, "undefine")
    return status

if __name__ == "__main__":
    sys.exit(main())
