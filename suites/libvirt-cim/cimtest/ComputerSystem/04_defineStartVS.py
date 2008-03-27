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

# This test case checks state of the VS is in enabled state after 
# defining and starting the  VS.
# By verifying the properties of EnabledState = 2 of the VS.
# 10-Oct-2007

import sys
from XenKvmLib import vxml
from XenKvmLib import computersystem
from VirtLib import utils
from CimTest import Globals
from CimTest.Globals import do_main
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV']
test_dom = "domguest"

@do_main(sup_types)
def main():
    options = main.options
    status = FAIL
    enabState = 0
    Globals.log_param()

    cxml = vxml.get_class(options.virt)(test_dom)
    cxml.define(options.ip)
    ret = cxml.start(options.ip)
    
    if not ret :
        Globals.logger.error("Failed to Start the dom: %s", test_dom)
        cxml.undefine(options.ip)
        return status

    try:
        cs = computersystem.get_cs_class(options.virt)(options.ip, test_dom)

        if cs.Name == test_dom:
            enabState = cs.EnabledState
        else:
            Globals.logger.error("VS %s is not defined" % test_dom)

        # Success: VS is in Enabled State after Define and Start 
        if enabState == 2:
            status = PASS

    except Exception, detail:
        Globals.logger.error(Globals.CIM_ERROR_GETINSTANCE, 
                             get_typed_class(options.virt, 'ComputerSystem'))
        Globals.logger.error("Exception: %s", detail)
        return status

    if status != PASS :
        Globals.logger.error("Error: property values are not set for VS %s" , test_dom)

    cxml.destroy(options.ip)
    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())

