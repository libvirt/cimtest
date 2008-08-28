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
# The test is considered to be successful if the request for the invalid
# state change from defined to suspend fails
#
# List of Valid state values (Refer to VSP spec doc Table 2 for more)
# ---------------------------------
# State             |   Values
# ---------------------------------
# Defined           |     3
# Suspend           |     9
#
# Date: 05-03-2008
#

import sys
import pywbem
from VirtLib import utils
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.test_doms import destroy_and_undefine_domain
from XenKvmLib.common_util import try_request_state_change, \
                                  create_using_definesystem

sup_types = ['Xen', 'XenFV', 'LXC', 'KVM']

SUSPEND_STATE = 9 
default_dom   = 'test_domain'
TIME          = "00000000000000.000000:000"
exp_rc        = pywbem.CIM_ERR_FAILED
exp_desc      = 'Domain not running'


@do_main(sup_types)
def main():
    options = main.options
    server = options.ip
    virt   = options.virt
    status = FAIL

    try:
        # define the vs
        status = create_using_definesystem(default_dom, server, virt=virt)
        if status != PASS:
            logger.error("Unable to define domain '%s' using DefineSystem()", 
                          default_dom)
            return status

    except Exception, details:
        logger.error("Exception: %s", details)
        destroy_and_undefine_domain(default_dom, server, virt)
        return FAIL

    status = try_request_state_change(default_dom, server,
                                      SUSPEND_STATE, TIME, exp_rc, 
                                      exp_desc, virt)

    if status != PASS:
        logger.error("Expected Defined -> Suspended state transition to fail")

    destroy_and_undefine_domain(default_dom, server, virt)
    return status 

if __name__ == "__main__":
    sys.exit(main())
