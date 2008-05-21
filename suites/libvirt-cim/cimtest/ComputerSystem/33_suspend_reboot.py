#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Anoop V Chakkalakkal<anoop.vijayan@in.ibm.com>
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
# has a value of 9 when the VS is moved from active to suspend state
# and has a value of 10 when rebooted
#
# List of Valid state values (Refer to VSP spec doc Table 2 for more)
# ---------------------------------
# State             |   Values
# ---------------------------------
# Defined           |     3
# Active            |     2
# Suspended         |     9
# Rebooted          |    10
#
#                                                   Date: 06-03-2008

import sys
from VirtLib import utils
from CimTest.Globals import do_main, logger
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC
from XenKvmLib.test_doms import undefine_test_domain
from XenKvmLib.common_util import get_cs_instance
from XenKvmLib.common_util import create_using_definesystem
from XenKvmLib.common_util import call_request_state_change

sup_types = ['Xen', 'XenFV']

ACTIVE_STATE = 2
SUSPND_STATE = 9
REBOOT_STATE = 10

bug         = "00001"
default_dom = 'test_domain'
TIME        = "00000000000000.000000:000"

def check_attributes(domain_name, ip, en_state, rq_state, virt):
    rc, cs = get_cs_instance(domain_name, ip, virt)
    if rc != 0:
        return rc
    if cs.RequestedState != rq_state:
        logger.error("RequestedState should be %d not %d", \
                     rq_state, cs.RequestedState)
        return FAIL
    if cs.EnabledState != en_state:
        logger.error("EnabledState should be %d not %d", \
                     en_state, cs.EnabledState)
        return FAIL
    return PASS

@do_main(sup_types)
def main():
    options = main.options
    status = FAIL

    tc_scen = [('Start',   [ACTIVE_STATE, ACTIVE_STATE]), \
               ('Suspend', [SUSPND_STATE, SUSPND_STATE]), \
               ('Reboot',  [SUSPND_STATE, REBOOT_STATE])]

    try:
        # define the vs
        status = create_using_definesystem(default_dom, options.ip,
                                           virt=options.virt)
        if status != PASS:
            logger.error("Unable to define domain %s using DefineSystem()", \
                                                                 default_dom)
            return status

        # start, suspend and reboot
        for action, state in tc_scen:
            en_state = state[0]
            rq_state = state[1]
            status = call_request_state_change(default_dom, options.ip,
                                               rq_state, TIME,
                                               virt=options.virt)
            if status != PASS:
                logger.error("Unable to %s dom %s using \
RequestedStateChange()", action, default_dom)
                status = XFAIL_RC(bug)
                break

            # FIX ME
            # sleep()

            status = check_attributes(default_dom, options.ip,
                                      en_state, rq_state, options.virt)
            if status != PASS:
                logger.error("Attributes for dom %s not set as expected.", \
                                                                default_dom)
                break

    except Exception, detail:
        logger.error("Exception: %s", detail)
        status = FAIL

    # undefine the vs
    undefine_test_domain(default_dom, options.ip, options.virt)

    return status

if __name__ == "__main__":
    sys.exit(main())
