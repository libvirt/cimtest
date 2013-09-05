#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Veerendra Chandrappa <vechandr@in.ibm.com>
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

# Edge Test case which verifies the assoc for the SystemDevice class with the 
# Xen_ComputerSystem Class. When passed with the wrong Key-Value combination
# for the association, the test case should exit with the expected error codes and desc.
# The association verifies for differnt combination of invalid values for all the classes

# Jan 04, 2008

import sys
import pywbem
from pywbem.cim_obj import CIMInstanceName
from XenKvmLib import vxml
from XenKvmLib import assoc
from XenKvmLib import enumclass
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest import Globals
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom = "virt1"
test_mac = "00:11:22:33:44:55"
test_cpu = 1

exp_rc1 = 1 #CIM_ERR_FAILED
exp_desc1 = "Missing DeviceID"
exp_rc2 = 6 #CIM_ERR_FAILED
exp_desc2 = "No such instance"

bug = 90443 # Got fixed :)

@do_main(sup_types)
def main():
    options = main.options

    if options.virt == 'Xen':
        test_disk = 'xvda'
    else:
        test_disk = 'vda'

    status = PASS
    virt_xml = vxml.get_class(options.virt)
    if options.virt == 'LXC':
        cxml = virt_xml(test_dom)
        devlist = ["Memory"]
    else:
        cxml = virt_xml(test_dom, vcpus = test_cpu, mac = test_mac,
                        disk = test_disk)
        devlist = [ "NetworkPort", "Memory", "LogicalDisk", "Processor" ]

    ret = cxml.cim_define(options.ip)
    if not ret :
        logger.error("Failed to define the domain '%s'",  test_dom)
        return FAIL

    status = cxml.cim_start(options.ip)
    if status != PASS :
        cxml.undefine(options.ip)
        logger.error("Failed to start the domain '%s'",  test_dom)
        return status 

    # Building the dict for avoiding the correct key:val pairs 
    # while verifying with the Invalid values for the association
    names = {}
    name = {}

    key_list = ["DeviceID", "CreationClassName", "SystemName",
                "SystemCreationClassName"]

    try:
        for item in devlist:
            cn = get_typed_class(options.virt, item)
            devs = enumclass.EnumInstances(options.ip, cn)
            if len(devs) == 0:
                raise Exception('empty result returned')
            for dev in devs:
                if dev.SystemName != test_dom:
                    continue

                name["DeviceID" , dev.DeviceID ] = item
                names[item] = ("DeviceID" , dev.DeviceID )

    except Exception, details:
        logger.info("Exception %s for class %s", details , item)
        cxml.cim_destroy(options.ip)
        cxml.cim_undefine(options.ip)
        return FAIL 

    if len(name) <=0 or len(names) <= 0:
        cxml.cim_destroy(options.ip)
        cxml.cim_undefine(options.ip)
        logger.info("Error: Could not find the device ID's")
        return FAIL

    conn = assoc.myWBEMConnection('http://%s' % options.ip, \
                                 (Globals.CIM_USER, Globals.CIM_PASS), 
                                  Globals.CIM_NS)

    # Testing with different combinations of keys and values 
    # for assocn of SysDevice class 
    key = [ "asdf", "virt1" , "DeviceID" ]
    val = [ "asdf", test_cpu-1, test_disk, test_mac , "mem"]

    for i in key:
        for j in val:

            #Building the keyval, for ex. keyval = 'domu/00:aa:bb:cc:dd:ee'
            keyval = test_dom + "/" + str (j)

            try:
                for item in devlist:
                    # In place of providing the 'key:keyvalue' combination 
                    # for the  DeviceId & values, giving wrong values
                    # by looping through.

   # Skipping the Association for the correct key:keyvalue combinations
   # For ex: i = 'DeviceID' keyval = 'virt1/00:aa:bb:cc:dd:ee' and 
   # item = Xen_NetworkPort

                    (a, b) = names[item]
                    if i == a and keyval == b and name[i, keyval] == item:
                        continue
                    cn = get_typed_class(options.virt, item)
                    instanceref = CIMInstanceName(cn, keybindings = {i : keyval , 
                                        "CreationClassName" : cn})

                    try:
                        sd_classname = get_typed_class(options.virt, 'SystemDevice')
                        conn.AssociatorNames(instanceref, 
                                             AssocClass = sd_classname)
                        rc = 0 

                    except pywbem.CIMError, (rc, desc):
                        if ((rc != exp_rc1 and desc.find(exp_desc1) <= 0) and 
                           (rc != exp_rc2 and desc.find(exp_desc2) <= 0)):
                            status = FAIL 
                            logger.info("Class = %s , key = %s , keyval = %s ",
                                        item, i, keyval)
                            logger.info("Unexpected rc %s and desc %s for %s",
                                        rc, desc, item)

                    except Exception, details:
                        logger.info("Unknown exception happened")
                        logger.info(details)
                        status = FAIL

                    if rc == 0:
                        logger.info("Success returned for wrong key and ID")
                        logger.info("Class = %s , key = %s , keyval = %s ",
                                    item, i , keyval)
                        cxml.cim_destroy(options.ip)
                        cxml.cim_undefine(options.ip)
                        return XFAIL_RC(bug)

            except Exception, details:
                logger.info("exception" , details)
                status = FAIL

    cxml.cim_destroy(options.ip)
    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())

