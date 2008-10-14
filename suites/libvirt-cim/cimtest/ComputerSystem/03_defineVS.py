#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
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

# This test case checks state of the VS is in disabled state after defining VS.
# By verifying the properties of EnabledState = 3 & PowerState = 8|6 of the VS.
# 26-Sep-2007

import sys
from XenKvmLib import enumclass
from XenKvmLib import vxml
from XenKvmLib.classes import get_typed_class
from VirtLib import utils
from CimTest import Globals
from XenKvmLib.const import do_main, VIRSH_ERROR_DEFINE
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
test_dom = "domU1"

@do_main(sup_types)
def main():
    options = main.options
    status = FAIL

    cxml = vxml.get_class(options.virt)(test_dom)
    rc = cxml.define(options.ip)
    if not rc:
        Globals.logger.error(VIRSH_ERROR_DEFINE % test_dom)
        return status

    cs_class = get_typed_class(options.virt, 'ComputerSystem')
    try:
        cs = enumclass.EnumInstances(options.ip, cs_class)
        if len(cs) == 0:
            raise Exception('No cs instance returned')
        for dom in cs:
            if dom.Name == test_dom:
                enabState = dom.EnabledState
                status = PASS
                break
        if status != PASS:
            raise Exception('No defined domain (%s) is found' % test_dom)
        else:
            status = FAIL # reverting back the flag value to 1

        # Success: Disabled State after Define, as expected
        if enabState == 3:
            status = PASS

    except Exception, detail:
        Globals.logger.error(Globals.CIM_ERROR_ENUMERATE, 
                             get_typed_class(options.virt, 'ComputerSystem'))
        Globals.logger.error("Exception: %s", detail)

    if status != PASS :
        Globals.logger.error("Error: property values are not set for VS %s" % test_dom)

    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())
