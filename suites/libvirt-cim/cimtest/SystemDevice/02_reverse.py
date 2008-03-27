#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Veerendra Chandrappa <vechandr@in.ibm.com>
#    Zhengang Li <lizg@cn.ibm.com>
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

import sys
from XenKvmLib.test_xml import testxml
from VirtLib import utils
from XenKvmLib import computersystem
from XenKvmLib import assoc
from XenKvmLib.test_doms import test_domain_function
from XenKvmLib import devices
from XenKvmLib.devices import Xen_NetworkPort, Xen_Memory, Xen_LogicalDisk, \
                       Xen_Processor
from CimTest.Globals import log_param, logger, do_main
from CimTest.ReturnCodes import PASS, FAIL 

sup_types = ['Xen']

test_dom = "test_domain"
test_mac = "00:11:22:33:44:55"

@do_main(sup_types)
def main():
    options = main.options

    log_param()
    status = FAIL
    test_xml = testxml(test_dom, mac = test_mac)
    test_domain_function(test_xml, options.ip, "destroy")
    test_domain_function(test_xml, options.ip, "create")

    devlist = [ "Xen_NetworkPort", "Xen_Memory", "Xen_LogicalDisk", \
                "Xen_Processor" ]

    key_list = ["DeviceID", "CreationClassName", "SystemName",
                "SystemCreationClassName"]
    for items in devlist:
        try:
            devs = devices.enumerate(options.ip, eval(items), key_list)
        except Exception, detail:
            logger.error("Exception: %s" % detail)
            test_domain_function(test_xml, options.ip, "destroy")
            return FAIL

        for dev in devs:
            if dev.SystemName != test_dom:
                continue

            try:
                systems = assoc.AssociatorNames(options.ip, "Xen_SystemDevice",
                            items, 
                            DeviceID=dev.DeviceID,
                            CreationClassName=dev.CreationClassName,
                            SystemName=dev.SystemName,
                            SystemCreationClassName=dev.SystemCreationClassName)
            except Exception, detail:
                logger.error("Exception: %s" % detail)
                test_domain_function(test_xml, options.ip, "destroy")
                return FAIL

            if systems == None:
                logger.error("Device association failed")
                test_domain_function(test_xml, options.ip, "destroy")
                return FAIL
            elif len(systems) != 1:
                logger.error("%s systems returned, expected 1" % len(systems))
                test_domain_function(test_xml, options.ip, "destroy")
                return FAIL

            system = computersystem.system_of(options.ip, systems[0])
        
            if system.Name == test_dom:
                status = PASS
                logger.info("Examined %s %s" % (system.Name, dev.DeviceID))
            else:
                logger.error("Association returned wrong system: %s" % 
                             system.Name)

    test_domain_function(test_xml, options.ip, "destroy")

    return status
        
if __name__ == "__main__":
    sys.exit(main())
