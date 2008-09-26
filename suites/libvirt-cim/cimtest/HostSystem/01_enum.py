#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
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

# Testcase which enumerates the Class Xen_HostSystem, 
# and verifies the hostname returned by the provider

import sys
from XenKvmLib import enumclass
from XenKvmLib.classes import get_typed_class
from VirtLib import live
from VirtLib import utils
from XenKvmLib.common_util import check_sblim
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL

SUPPORTED_TYPES = ['Xen', 'KVM', 'XenFV', 'LXC']

@do_main(SUPPORTED_TYPES)
def main():
    options = main.options
    host = live.hostname(options.ip) 
   
    status = FAIL
    keys = ['Name', 'CreationClassName']
    name = get_typed_class(options.virt, 'HostSystem')
    
    ret, linux_cs = check_sblim(options.ip, options.virt)
    try:
        hs = enumclass.enumerate(options.ip, 'HostSystem', keys, options.virt)
    except Exception, details:
        logger.error("%s %s: %s" % (CIM_ERROR_ENUMERATE, name, details))
        status = FAIL

    if ret == PASS:
        if len(hs) != 0:
            logger.error("Unexpected instance returned")
            return FAIL
        else:
            if linux_cs.CreationClassName != 'Linux_ComputerSystem'\
              or linux_cs.Name != host:
                logger.error("Exp Linux_ComputerSystem, got %s" \
                             % linux_cs.CreationClassName)
                logger.error("Exp %s, got %s" % (host, system.Name))
                return FAIL
            else:
                return PASS
    else:
        if len(hs) != 1:
            logger.error("Expected 1 %s instance returned" % name)
            return FAIL
   
        system = hs[0]

        if system.CreationClassName != name or system.Name != host:
            logger.error("Exp %s, got %s" % (name, system.CreationClassName))
            logger.error("Exp %s, got %s" % (host, system.Name))
            status = FAIL
        else:
            logger.info("%s is %s" % (name, host))
            status = PASS

    return status

if __name__ == "__main__":
    sys.exit(main())
