#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Anoop V Chakkalakkal<anoop.vijayan@in.ibm.com>
#    Deepti B. Kalakeri<deeptik@linux.vnet.ibm.com>
#
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
# has a value of 2 when the VS is moved from defined to active state and
# and has a value of 11 when reset
#
# List of Valid state values (Refer to VSP spec doc Table 2 for more)
# ---------------------------------
# State             |   Values
# ---------------------------------
# Defined           |     3
# Active            |     2
# Reset             |    11
#
#                                                   Date: 06-03-2008

import sys
from VirtLib import utils
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.test_doms import destroy_and_undefine_domain
from XenKvmLib.common_util import get_cs_instance, create_using_definesystem, \
                                  call_request_state_change, \
                                  poll_for_state_change

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']

ACTIVE_STATE = 2
RESET_STATE  = 11

default_dom = 'cs_test_domain'
TIME        = "00000000000000.000000:000"

@do_main(sup_types)
def main():
    options = main.options
    status = FAIL
    server = options.ip
    virt   = options.virt

    tc_scen = [('Start', [ACTIVE_STATE, ACTIVE_STATE]), 
               ('Reset', [ACTIVE_STATE, RESET_STATE])]

    try:
        # define the vs
        status = create_using_definesystem(default_dom, server,
                                           virt=virt)
        if status != PASS:
            logger.error("Unable to define domain '%s' using DefineSystem()", 
                          default_dom)
            return status

        # start and reset
        for action, state in tc_scen:
            en_state = state[0]
            rq_state = state[1]
            status = call_request_state_change(default_dom, server,
                                               rq_state, TIME,
                                               virt=virt)
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
        logger.error("Exception: %s", detail)
        status = FAIL

    destroy_and_undefine_domain(default_dom, server, virt)
    return status

if __name__ == "__main__":
    sys.exit(main())
