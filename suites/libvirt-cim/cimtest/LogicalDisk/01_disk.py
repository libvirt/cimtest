#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
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
import pywbem
from VirtLib import utils
from XenKvmLib.enumclass import GetInstance
from XenKvmLib.classes import get_typed_class
from XenKvmLib.vxml import XenXML, KVMXML, get_class
from CimTest.Globals import logger
from XenKvmLib.const import do_main

SUPPORTED_TYPES = ['Xen', 'KVM', 'XenFV']

test_dom = "test_domain"

@do_main(SUPPORTED_TYPES)
def main():
    options = main.options
    if options.virt == 'Xen':
       test_dev = 'xvda'
    else:
       test_dev = 'hda'

    vsxml = get_class(options.virt)(test_dom, disk=test_dev)
    vsxml.cim_define(options.ip)
  
    devid = "%s/%s" % (test_dom, test_dev)
    disk = get_typed_class(options.virt, "LogicalDisk")
    key_list = { 'DeviceID' : devid,
                 'CreationClassName' : disk,
                 'SystemName' : test_dom,
                 'SystemCreationClassName' : get_typed_class(options.virt, "ComputerSystem")
               }
    dev = GetInstance(options.ip, disk, key_list)
    status = 0
    
    if dev is None:
        logger.error("GetInstance() returned None")
        status = 1
    elif dev.Name != test_dev:
        logger.error("Name should be `%s' instead of `%s'", test_dev, dev.Name)
        status = 1

    if status == 0:
        logger.info("Checked device %s", dev.Name)

    vsxml.undefine(options.ip)
    
    return status

if __name__ == "__main__":
    sys.exit(main())
