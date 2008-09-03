#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
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
from XenKvmLib import enumclass
from VirtLib import live
from VirtLib import utils
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL, SKIP

sup_types = ['KVM', 'LXC']

def clean_system(host, virt):
    l = live.domain_list(host, virt)
    if len(l) > 0:
        return False
    else:
        return True

@do_main(sup_types)
def main():
    options = main.options

    if not clean_system(options.ip, options.virt):
        logger.error("System has defined domains; unable to run")
        return SKIP 

    cn = "%s_ComputerSystem" % options.virt

    keys = ['Name', 'CreationClassName']
    try:
        cs = enumclass.enumerate(options.ip, 'ComputerSystem', keys, options.virt)

    except Exception, details:
        logger.error(CIM_ERROR_ENUMERATE, cn)
        logger.error(details)
        return FAIL
    
    if len(cs) != 0:
        logger.error("%s returned %d instead of empty list" % (cn, len(cs)))
        status = FAIL
    else:
        status = PASS

    return status 

if __name__ == "__main__":
    sys.exit(main())
