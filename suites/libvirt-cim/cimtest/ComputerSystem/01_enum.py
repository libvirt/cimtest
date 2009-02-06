#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Veerendra Chandrappa <vechandr@in.ibm.com>
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
from XenKvmLib.const import do_main
from XenKvmLib import enumclass
from XenKvmLib.xm_virt_util import domain_list
from XenKvmLib.classes import get_typed_class
from VirtLib import utils
from CimTest import Globals
from CimTest.ReturnCodes import PASS, FAIL

SUPPORTED_TYPES = ['Xen', 'KVM', 'XenFV', 'LXC']

@do_main(SUPPORTED_TYPES)
def main():
    options = main.options 
    status = PASS

    cs_class = get_typed_class(options.virt, 'ComputerSystem')
    try:
        cs = enumclass.EnumInstances(options.ip, cs_class)
        live_cs = domain_list(options.ip, options.virt)
        for system in cs:
            name = system.name
            try:
                idx = live_cs.index(name)
                del live_cs[idx]
            except ValueError, detail:
                Globals.logger.error("Provider reports system `%s', \
but virsh does not", name)
                status = FAIL

        for system in live_cs:
            Globals.logger.error("Provider does not report system `%s', \
but virsh does", system)
            status = FAIL

    except IndexError, detail:
        Globals.logger.error("Exception: %s", detail)
    except Exception, detail:
        Globals.logger.error(Globals.CIM_ERROR_ENUMERATE, 'ComputerSystem')
        Globals.logger.error("Exception: %s", detail)

    return status

if __name__ == "__main__":
    sys.exit(main())
