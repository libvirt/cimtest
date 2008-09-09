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
from XenKvmLib import devices
from XenKvmLib.classes import get_typed_class
from XenKvmLib.vxml import XenXML, KVMXML, get_class
from CimTest.Globals import logger
from XenKvmLib.const import do_main

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom = "test_domain"
mem = 256 #MB

@do_main(sup_types)
def main():
    options = main.options
    
    vsxml = get_class(options.virt)(test_dom, mem)
    vsxml.cim_define(options.ip)
    alloc_mem = int(vsxml.xml_get_mem())
    
    devid = "%s/mem" % test_dom
    key_list = { 'DeviceID' : devid,
                 'CreationClassName' : get_typed_class(options.virt, "Memory"),
                 'SystemName' : test_dom,
                 'SystemCreationClassName' : get_typed_class(options.virt, "ComputerSystem")
               }
    dev = eval('devices.' + get_typed_class(options.virt, "Memory"))(options.ip, key_list)

    status = 0

    if dev.ConsumableBlocks > dev.NumberOfBlocks:
        logger.error("ConsumableBlocks should not be larger than NumberOfBlocks")
        status = 1

    capacity = dev.ConsumableBlocks * dev.BlockSize / 1024 

    if capacity != alloc_mem:
        logger.error("Capacity should be %i MB instead of %i MB" % (alloc_mem, capacity))
        status = 1

    if status == 0:
        logger.info("Checked memory capacity: %s MB" % capacity)

    vsxml.undefine(options.ip)
    return status


if __name__ == "__main__":
    sys.exit(main())
    
