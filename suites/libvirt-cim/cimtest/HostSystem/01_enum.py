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
from CimTest.Globals import do_main
from XenKvmLib import hostsystem
from XenKvmLib.classes import get_typed_class
from VirtLib import live
from VirtLib import utils
from CimTest import Globals
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL

SUPPORTED_TYPES = ['Xen', 'KVM', 'XenFV']

@do_main(SUPPORTED_TYPES)
def main():
    options = main.options
    status = PASS
    host = live.hostname(options.ip) 
   
    try:
        hs = hostsystem.enumerate(options.ip, options.virt)
        name = get_typed_class(options.virt, 'HostSystem')
        
        for system in hs:
            if system.CreationClassName != name and system.Name != host:
                logger.error("%s Enumerate Instance error" % name)
                status = FAIL
            else:
                logger.info("%s is %s" % (name, host))

    except BaseException:
        logger.error(Globals.CIM_ERROR_ENUMERATE % hostsystem.CIM_System)
        status = FAIL

    return status

if __name__ == "__main__":
    sys.exit(main())
