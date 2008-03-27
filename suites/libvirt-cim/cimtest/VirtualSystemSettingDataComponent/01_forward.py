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
from CimTest.Globals import log_param, logger, do_main

sup_types = ['Xen']

test_dom    = "VSSDC_dom"
test_vcpus  = 2
test_mac    = "00:11:22:33:44:aa"
test_disk   = 'xvda'
status      = 0
VSType      = "Xen"
vssd_names  = []
vssd_values = []

RASD_cllist = [
          'Xen_DiskResourceAllocationSettingData', \
          'Xen_MemResourceAllocationSettingData',  \
          'Xen_NetResourceAllocationSettingData',  \
          'Xen_ProcResourceAllocationSettingData'
         ]
          
def init_list():
    """
        Creating the lists that will be used for comparisons.
    """
    prop_list = [] 
    prop_list = ["%s/%s"  % (test_dom, test_disk), \
                 "%s/%s" % (test_dom, "mem"), \
                 "%s/%s" % (test_dom, test_mac)
                ]
    proc_list = []
    for i in range(test_vcpus):
        proc_list.append("%s/%s" % (test_dom, i))
    return prop_list, proc_list

def build_vssd_info(ip, vssd):
    """
        Creating the vssd fileds lists that will be used for comparisons.
    """
    global vssd_names, vssd_values

    if vssd.Bootloader == "" or vssd.Caption == "" or \
      vssd.InstanceID == "" or vssd.ElementName == "" or \
      vssd.VirtualSystemIdentifier == "" or vssd.VirtualSystemType == "":
        logger.error("One of the required VSSD details seems to be empty")
        status = 1
        test_domain_function(test_dom, ip, "undefine")
        sys.exit(status)
 
    vssd_names = [
                  'Bootloader',    \
                  'Caption',       \
                  'InstanceID',    \
                  'ElementName',   \
        'VirtualSystemIdentifier', \
              'VirtualSystemType', \
    ]
       
    vssd_values = [
                    vssd.Bootloader,  \
                       vssd.Caption,  \
                     vssd.InstanceID, \
                    vssd.ElementName, \
        vssd.VirtualSystemIdentifier, \
              vssd.VirtualSystemType, \
       ]


def assoc_values(ip, assoc_info, cn):
    """
        The association info of 
        Xen_VirtualSystemSettingDataComponent with every RASDclass is
        verified for following fields:
        Caption, InstanceID, ElementName, VirtualSystemIdentifier,
        VirtualSystemType, Bootloader
    """
    global status
    global vssd_names, vssd_values

    try: 
        if len(assoc_info) != 1:
            Globals.logger.error("Xen_VirtualSystemSettingDataComponent \
returned %i Resource objects for class '%s'", len(assoc_info),cn)
            status = 1
            return status

        for idx in range(len(vssd_names)):
            if assoc_info[0][vssd_names[idx]] != vssd_values[idx]:
                Globals.logger.error("%s Mismatch", vssd_names[idx])
                Globals.logger.error("Returned %s instead of %s", \
                               assoc_info[0][vssd_names[idx]], \
                                                vssd_fields[idx])
                status = 1
            if status != 0:
                break
    except  Exception, detail :
        logger.error("Exception in assoc_values function: %s" % detail)
        status = 1
        test_domain_function(test_dom, ip, "undefine")
        return status


@do_main(sup_types)
def main():
    options = main.options
    global  status 

    log_param()
    destroy_and_undefine_all(options.ip)
    test_xml = testxml_bl(test_dom, vcpus = test_vcpus, \
                          mac = test_mac, disk = test_disk, \
                          server = options.ip,\
                          gtype = 0)
    ret = test_domain_function(test_xml, options.ip, cmd = "define")
    if not ret:
        logger.error("Failed to define the dom: %s", test_dom)
        status = 1
        return status


    instIdval = "%s:%s" % (VSType, test_dom)
    keyname = "InstanceID"

    key_list = { 'InstanceID' : instIdval }
    try:
        vssd = enumclass.getInstance(options.ip, \
                                    enumclass.Xen_VirtualSystemSettingData, \
                                    key_list)
        build_vssd_info(options.ip, vssd)

    except  Exception, detail :
        logger.error(Globals.CIM_ERROR_GETINSTANCE, \
                                            'Xen_VirtualSystemSettingData')
        logger.error("Exception : %s" % detail)
        test_domain_function(test_dom, options.ip, "undefine")
        status = 1
        return status

    prop_list, proc_list = init_list() 

    try:
        idx = 0
    # Looping through the RASD_cllist, call association 
    # Xen_VirtualSystemSettingDataComponent with each class in RASD_cllist
        for rasd_cname in RASD_cllist:
            if rasd_cname != 'Xen_ProcResourceAllocationSettingData':
                assoc_info = assoc.Associators(options.ip, \
                                     'Xen_VirtualSystemSettingDataComponent', \
                                                                  rasd_cname, \
                                                   InstanceID = prop_list[idx])
             # Verify the association fields returned for particular rasd_cname.
                assoc_values(options.ip, assoc_info, rasd_cname)
                idx = idx + 1
            else:
            # Xen_ProcResourceAllocationSettingData, we need to find 
            # association information for all the proc InstanceID and hence 
            # we loop from 0 to (test_vcpus - 1 )
                for index in range(len(proc_list)):  
                    assoc_info = assoc.Associators(options.ip, \
                                    'Xen_VirtualSystemSettingDataComponent', \
                                                                  rasd_cname, \
                                                  InstanceID = prop_list[index])
            # Verify the association fields returned for particular rasd_cname.
                    assoc_values(options.ip, assoc_info, rasd_cname)
 
    except  Exception, detail :
        logger.error(Globals.CIM_ERROR_ASSOCIATORS, \
                                      'Xen_VirtualSystemSettingDataComponent')
        logger.error("Exception : %s" % detail)
        status = 1 

    test_domain_function(test_dom, options.ip, "undefine")
    return status

if __name__ == "__main__":
    sys.exit(main())
