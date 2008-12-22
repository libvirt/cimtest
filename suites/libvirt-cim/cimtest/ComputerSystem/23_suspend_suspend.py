#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Anoop V Chakkalakkal<anoop.vijayan@in.ibm.com>
#    Deepti B. Kalakeri<deeptik@linux.vnet.ibm.com>
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# Test Case Info:
# --------------
# This test case is used to verify the Virtual System State Transition
# information is captured in the RequestedState Property of the VS.
# The test is considered to be successful if RequestedState Property
# has a value of 9 when the VS is moved from active to suspend state
# and returns an excpetion when supended again.
#
# List of Valid state values (Refer to VSP spec doc Table 2 for more)
# ---------------------------------
# State             |   Values
# ---------------------------------
# Defined           |     3
# Active            |     2
# Suspended         |     9
#
# Date: 29-02-2008

import sys
import pywbem
from VirtLib import utils
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC
from XenKvmLib.test_doms import destroy_and_undefine_domain
from XenKvmLib.common_util import create_using_definesystem, \
                                  call_request_state_change, \
                                  try_request_state_change, \
                                  poll_for_state_change

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']

ACTIVE_STATE = 2
SUSPND_STATE = 9

default_dom = 'cs_test_domain'
TIME        = "00000000000000.000000:000"
err_no = pywbem.CIM_ERR_FAILED
err_desc = "Domain not running"

bug_libvirt = "00011"

@do_main(sup_types)
def main():
    options = main.options
    server  = options.ip
    virt    = options.virt

    tc_scen = [('Start',   [ACTIVE_STATE, ACTIVE_STATE]), \
               ('Suspend', [SUSPND_STATE, SUSPND_STATE])] 
    try:
        # define the vs
        status = create_using_definesystem(default_dom, 
                                           server, 
                                           virt=virt)
        if status != PASS:
            logger.error("Unable to define domain '%s' using DefineSystem()", 
                          default_dom)
            return status

        # start, suspend 
        for action, state in tc_scen:
            en_state = state[0]
            rq_state = state[1]
            status = call_request_state_change(default_dom, server,
                                               rq_state, TIME, virt)
            if status != PASS:
                logger.error("Unable to '%s' dom '%s' using RequestedStateChange()",
                              action, default_dom)
                break

            status, dom_cs = poll_for_state_change(server, virt, default_dom, en_state, 
                                                   timeout=30)
            if status != PASS or dom_cs.RequestedState != rq_state:
                status = FAIL
                logger.error("Attributes for dom '%s' is not set as expected.", 
                              default_dom)
                break

    except Exception, detail:
        logger.error("Exception: '%s'", detail)
        status = FAIL

    if status != PASS:
        destroy_and_undefine_domain(default_dom, server, virt)
        if virt == 'LXC':
            return XFAIL_RC(bug_libvirt)
        return status

    # try to suspend already suspended VS
    rq_state = SUSPND_STATE
    status = try_request_state_change(default_dom, server,
                                      rq_state, TIME, err_no, 
                                      err_desc, virt)

    destroy_and_undefine_domain(default_dom, server, virt)

    return status

if __name__ == "__main__":
    sys.exit(main())
