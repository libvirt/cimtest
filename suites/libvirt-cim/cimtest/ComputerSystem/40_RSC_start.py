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
from XenKvmLib.test_doms import destroy_and_undefine_domain 
from XenKvmLib.common_util import *
from CimTest.Globals import logger
from CimTest.Globals import do_main
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV']

default_dom = 'cs_test_domain'
REQUESTED_STATE = 2
TIME = "00000000000000.000000:000"

@do_main(sup_types)
def main():
    options = main.options
    server = options.ip
    virt = options.virt
    status = FAIL

    status, test_network = create_netpool_conf(server, virt, False)
    if status != PASS:
        return FAIL

    try:
        rc = create_using_definesystem(default_dom, server, 
                                       virt=virt)
        if rc != 0:
            status = FAIL
            raise Exception("DefineSystem() failed to create domain: '%s'" % 
                            default_dom)

        rc = call_request_state_change(default_dom, server, 
                                       REQUESTED_STATE, TIME, virt)
        if rc != 0:
            status = FAIL
            raise Exception("RequestedStateChange() could not be used to start"
                            " domain: '%s'" % default_dom)

        status, dom_cs = poll_for_state_change(server, virt, default_dom, 
                                               REQUESTED_STATE, timeout=10)

        if status != PASS or dom_cs.RequestedState != REQUESTED_STATE:
            status = FAIL
            raise Exception("Attributes were not set as expected for "
                            "domain: '%s'" % default_dom)
        else:
            status = PASS

    except Exception, detail:
        logger.error("Exception: %s", detail)

    destroy_netpool(server, virt, test_network)
    destroy_and_undefine_domain(default_dom, server, virt)
    return status

if __name__ == "__main__":
    sys.exit(main())
    
