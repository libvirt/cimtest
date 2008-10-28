#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
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
import pywbem
from VirtLib import utils
from VirtLib import live
from XenKvmLib.enumclass import GetInstance
from XenKvmLib.test_xml import testxml
from XenKvmLib.classes import get_typed_class
from XenKvmLib.vxml import XenXML, KVMXML, get_class
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL

SUPPORTED_TYPES = ['Xen', 'KVM', 'XenFV']

test_dom = "domain"
test_vcpus = 1

@do_main(SUPPORTED_TYPES)
def main():
    options = main.options
    status = PASS
    vsxml = get_class(options.virt)(test_dom, vcpus=test_vcpus)
    vsxml.define(options.ip)
    vsxml.start(options.ip)

    # Processor instance enumerate need the domain to be active
    domlist = live.active_domain_list(options.ip, options.virt)
    proc_class = get_typed_class(options.virt, "Processor")
    if test_dom not in domlist:
        status = FAIL
        logger.error("Domain not started, we're not able to check vcpu")
    else:
        for i in range(0, test_vcpus):
            devid = "%s/%s" % (test_dom, i)
            key_list = { 'DeviceID' : devid,
                         'CreationClassName' : proc_class,
                         'SystemName' : test_dom,
                         'SystemCreationClassName' : get_typed_class(options.virt, "ComputerSystem")
                       }
            try:
                dev = GetInstance(options.ip, proc_class, key_list)
                if dev.DeviceID == devid:
                    logger.info("Checked device %s" % devid)
                else:
                    logger.error("Mismatching device, returned %s instead %s" % (dev.DeviceID, devid))
            except Exception, details:
                logger.error("Error check device %s: %s" % (devid, details))
                status = 1

    vsxml.stop(options.ip)
    vsxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())
