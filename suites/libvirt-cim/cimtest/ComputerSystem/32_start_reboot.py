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
# has a value of 10 when the VS is moved from active to reboot state.
#
# List of Valid state values (Refer to VSP spec doc Table 2 for more)
# ---------------------------------
# State             |   Values
# ---------------------------------
# Defined           |     3
# Active            |     2
# Rebooted          |     10
#
# Date: 03-03-2008

import sys
from VirtLib import utils
from CimTest.Globals import do_main, logger
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC
from XenKvmLib.test_doms import destroy_and_undefine_domain
from XenKvmLib.common_util import create_using_definesystem
from XenKvmLib.common_util import call_request_state_change
from XenKvmLib.common_util import poll_for_state_change
from XenKvmLib.common_util import create_netpool_conf, destroy_netpool

sup_types = ['Xen', 'XenFV', 'KVM']

bug_libvirt     = "00005"
ACTIVE_STATE = 2
REBOOT_STATE = 10
default_dom = 'cs_test_domain'
TIME        = "00000000000000.000000:000"

@do_main(sup_types)
def main():
    options = main.options
    status = FAIL
    server = options.ip
    virt   = options.virt

    status, test_network = create_netpool_conf(server, virt, False)
    if status != PASS:
        return FAIL

    tc_scen = [('Start',  [ACTIVE_STATE, ACTIVE_STATE]), \
               ('Reboot', [ACTIVE_STATE, REBOOT_STATE])]

    try:
        # define the vs
        status = create_using_definesystem(default_dom, server,
                                           virt=virt)
        if status != PASS:
            logger.error("Unable to define domain '%s' using DefineSystem()", 
                          default_dom)
            return status

        # start, then reboot
        for action, state in tc_scen:
            en_state = state[0]
            rq_state = state[1]
            status = call_request_state_change(default_dom, server,
                                               rq_state, TIME,
                                               virt=virt)
            if status != PASS:
                logger.error("Unable to '%s' dom '%s' using RequestedStateChange()", 
                              action, default_dom)
                status = XFAIL_RC(bug_libvirt)
                break

            status, dom_cs = poll_for_state_change(server, virt, default_dom, en_state,
                                           timeout=10)

            if status != PASS or dom_cs.RequestedState != rq_state:
                status = FAIL
                logger.error("Attributes for dom '%s' is not set as expected.",
                              default_dom)
                break

    except Exception, detail:
        logger.error("Exception: %s", detail)
        status = FAIL

    destroy_netpool(server, virt, test_network)
    destroy_and_undefine_domain(default_dom, server, virt)
    return status

if __name__ == "__main__":
    sys.exit(main())
