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
from VirtLib import utils
from XenKvmLib import vxml
from XenKvmLib import enumclass
from XenKvmLib import assoc
from XenKvmLib import devices
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL 
from XenKvmLib.common_util import get_typed_class

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom = "test_domain"
test_mac = "00:11:22:33:44:55"

@do_main(sup_types)
def main():
    options = main.options

    status = FAIL
    virt_xml = vxml.get_class(options.virt)
    if options.virt == 'LXC':
        cxml = virt_xml(test_dom)
        devlist = ["Memory"]
    else:
        cxml = virt_xml(test_dom, mac=test_mac)
        devlist = [ "NetworkPort", "Memory", "LogicalDisk", "Processor",
                    "PointingDevice", "DisplayController" ]
    cxml.create(options.ip)


    key_list = ["DeviceID", "CreationClassName", "SystemName",
                "SystemCreationClassName"]
    for items in devlist:
        cn = get_typed_class(options.virt, items)
        try:
            devs = enumclass.EnumInstances(options.ip, cn)
        except Exception, detail:
            logger.error("Exception: %s", detail)
            cxml.destroy(options.ip)
            cxml.undefine(options.ip)
            return FAIL

        for dev in devs:
            if dev.SystemName != test_dom:
                continue

            try:
                an = get_typed_class(options.virt, "SystemDevice")
                cn = dev.CreationClassName
                systems = assoc.AssociatorNames(options.ip, an, cn, 
                                                DeviceID=dev.DeviceID,
                                                CreationClassName=cn,
                                                SystemName=dev.SystemName,
                                                SystemCreationClassName=dev.SystemCreationClassName)
            except Exception, detail:
                logger.error("Exception: %s", detail)
                cxml.destroy(options.ip)
                cxml.undefine(options.ip)
                return FAIL

            if systems == None:
                logger.error("Device association failed")
                cxml.destroy(options.ip)
                cxml.undefine(options.ip)
                return FAIL
            elif len(systems) != 1:
                logger.error("%s systems returned, expected 1", len(systems))
                cxml.destroy(options.ip)
                cxml.undefine(options.ip)
                return FAIL
            
            keys = {
                    'Name': systems[0]['Name'],
                    'CreationClassName': systems[0]['CreationClassName']
                   }
            cn = get_typed_class(options.virt, 'ComputerSystem')
            system = enumclass.GetInstance(options.ip, cn, keys)
        
            if system.Name == test_dom:
                status = PASS
                logger.info("Examined %s %s", system.Name, dev.DeviceID)
            else:
                logger.error("Association returned wrong system: %s", 
                             system.Name)

    cxml.destroy(options.ip)
    cxml.undefine(options.ip)

    return status
        
if __name__ == "__main__":
    sys.exit(main())
