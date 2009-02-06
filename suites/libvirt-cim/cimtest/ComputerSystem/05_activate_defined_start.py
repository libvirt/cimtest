#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
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

# This test case is used to verify the Virtual System State Transition,
# information related to this is captured in the RequestedState Property
# of the VS.
# The test is considered to be successful if RequestedState Property 
# has a value of "2" when the VS is moved from defined to activate state.
#
#						Date  : 17-10-2007

import sys
from XenKvmLib.enumclass import GetInstance 
from XenKvmLib.vxml import get_class
from CimTest.Globals import logger
from XenKvmLib.const import do_main, CIM_ENABLE, CIM_DISABLE
from XenKvmLib.classes import get_typed_class
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
test_dom = "DomST1"

@do_main(sup_types)
def main():
    options = main.options
    status = FAIL

    cxml = get_class(options.virt)(test_dom) 
    ret = cxml.cim_define(options.ip)
    #Define a VS
    if not ret :
        logger.error("ERROR: VS '%s' was not defined", test_dom)
        return status 

    try:
        status = cxml.check_guest_state(options.ip, CIM_DISABLE, 0)
        if status != PASS:
            raise Exception("%s not in expected state" % test_dom)

        #Change the state of the  VS to Start
        status = cxml.cim_start(options.ip)
        if status != PASS:      
            raise Exception("Unable start dom '%s'" % test_dom)

        #Get the value of the EnabledState property and RequestedState property.
        status = cxml.check_guest_state(options.ip, CIM_ENABLE)
        if status != PASS:
            raise Exception("%s not in expected state" % test_dom)

    except Exception, detail:
        logger.error("Exception: %s", detail)
        status = FAIL

    cxml.cim_destroy(options.ip)
    cxml.undefine(options.ip)
    return status
if __name__ == "__main__":
    sys.exit(main())
