#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
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
from time import sleep
from XenKvmLib import enumclass
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL, SKIP

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom = "test_domain"
def clean_system(host, virt='Xen'):
    timer_count = 10
    for count in range(0, timer_count):
        cs = get_typed_class(virt, 'ComputerSystem')
        l = enumclass.EnumInstances(host, cs)
        if len(l) == 0:
            return True
        if virt == 'Xen' or virt == 'XenFV':
            sleep(1)
        else:
            break
    return False

@do_main(sup_types)
def main():
    options = main.options
    if not clean_system(options.ip, options.virt):
        logger.error("System has defined domains; unable to run")
        return SKIP

    key_list = ["DeviceID", "CreationClassName", "SystemName", 
                "SystemCreationClassName"]

    cn = get_typed_class(options.virt, "LogicalDisk")

    try:
        devs = enumclass.EnumInstances(options.ip, cn)

    except Exception, details:
        logger.error(CIM_ERROR_ENUMERATE, cn)
        logger.error(details)
        return FAIL

    if len(devs) != 0:
        logger.error("%s returned %d instead of empty list", cn, len(devs))
        status = FAIL
    else:
        status = PASS 

    return status

if __name__ == "__main__":
    sys.exit(main())
    
