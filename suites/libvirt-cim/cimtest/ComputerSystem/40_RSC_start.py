#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
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

# This test case defines a guest using DefineSystem().  The guest is then
# started (put in the "Active" state) using RequestStateChange(). 

# Steps:
#  1. Define a guest using DefineSystem().
#  2. Get the CIM instance of the guest created using DefineSystem().
#  3. Start the guest using RequestStateChange().
#  4. Get the CIM instance of the guest again - should have different values
#     for its attributes based on the state change.
#  5. Verify the instance attributes are correct after the state change. 
#

import sys
import pywbem
from VirtLib import utils
from XenKvmLib.test_doms import undefine_test_domain 
from XenKvmLib.common_util import *
from CimTest.Globals import logger
from CimTest.Globals import do_main
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC

sup_types = ['Xen', 'KVM', 'XenFV']
bug = "00001"

default_dom = 'test_domain'
REQUESTED_STATE = 2
TIME = "00000000000000.000000:000"

def check_attributes(domain_name, ip, virt):
    rc, cs = get_cs_instance(domain_name, ip, virt)
    if rc != 0:
        return rc 

    if cs.RequestedState != REQUESTED_STATE:
        logger.error("RequestedState should be %d not %d",
                     REQUESTED_STATE, cs.RequestedState)
        return FAIL

    if cs.EnabledState != REQUESTED_STATE:
        logger.error("EnabledState should be %d not %d",
                     REQUESTED_STATE, cs.EnabledState)
        return FAIL

    return PASS

@do_main(sup_types)
def main():
    options = main.options
    status = PASS 

    try:
        rc = create_using_definesystem(default_dom, options.ip, 
                                       virt=options.virt)
        if rc != 0:
            raise Exception("Unable create domain %s using DefineSystem()", 
                            default_dom)

        rc = call_request_state_change(default_dom, options.ip, 
                                       REQUESTED_STATE, TIME, options.virt)
        if rc != 0:
            rc = XFAIL_RC(bug)
            raise Exception("Unable start dom %s using RequestedStateChange()", 
                            default_dom)

        rc = check_attributes(domain_name, ip, options.virt)
        if rc != 0:
            raise Exception("Attributes for %s not set as expected.",
                            default_dom)

    except Exception, detail:
        logger.error("Exception: %s", detail)
        status = rc

    undefine_test_domain(default_dom, options.ip, options.virt)

    return status

if __name__ == "__main__":
    sys.exit(main())
    
