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
from XenKvmLib import assoc
from XenKvmLib.test_doms import test_domain_function
from XenKvmLib import devices
from CimTest.Globals import log_param, logger, do_main
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen']

test_dom = "test_domain"
test_mac = "00:11:22:33:44:55"
test_disk = "xvdb"
test_cpu = 1

@do_main(sup_types)
def main():
    options= main.options

    log_param()
    status = PASS
    test_xml = testxml(test_dom, vcpus = test_cpu, mac = test_mac, \
                       disk = test_disk)

    test_domain_function(test_xml, options.ip, "destroy")
    test_domain_function(test_xml, options.ip, "create")

    devs = assoc.AssociatorNames(options.ip, "Xen_SystemDevice",
                                 "Xen_ComputerSystem", 
                                 Name=test_dom,
                                 CreationClassName="Xen_ComputerSystem")
    if devs == None:
        logger.error("System association failed")
        return FAIL
    elif len(devs) == 0:
        logger.error("No devices returned")
        return FAIL

    devlist = ["Xen_NetworkPort", "Xen_Memory", "Xen_LogicalDisk", \
               "Xen_Processor"]

    key_list = {'DeviceID' : '',
                'CreationClassName' : '',
                'SystemName' : test_dom,
                'SystemCreationClassname' : "Xen_ComputerSystem"
               }
 
    for items in devlist:
        for dev in devs:
            key_list['CreationClassName'] = dev['CreationClassname']
            key_list['DeviceID'] = dev['DeviceID']
            device = devices.device_of(options.ip, key_list)
            if device.CreationClassName != items:
                continue
            devid = device.DeviceID

            if items == "Xen_NetworkPort":
                _devid = "%s/%s" % (test_dom, test_mac)
            elif items == "Xen_LogicalDisk":
                _devid = "%s/%s" % (test_dom, test_disk)
            elif items == "Xen_Processor":
                _devid = "%s/%d" % (test_dom, test_cpu-1)
            elif items == "Xen_Memory":
                _devid = "%s/mem" % test_dom
                
            if devid != _devid:
                logger.error("DeviceID `%s` != `%s'" % (devid, _devid))
                status = FAIL
            else:
                logger.info("Examined %s" % _devid)
            
    test_domain_function(test_xml, options.ip, "destroy")

    return status
        
if __name__ == "__main__":
    sys.exit(main())
