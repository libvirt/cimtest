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
from CimTest.Globals import do_main, logger
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.test_doms import undefine_test_domain
from XenKvmLib.common_util import get_cs_instance
from XenKvmLib.common_util import create_using_definesystem

sup_types = ['Xen', 'XenFV', 'LXC']

SUSPEND_STATE = 9 
default_dom   = 'test_domain'
TIME          = "00000000000000.000000:000"
exp_rc        = pywbem.CIM_ERR_FAILED
exp_desc      = 'Domain not running'

@do_main(sup_types)
def main():
    options = main.options

    try:
        # define the vs
        status = create_using_definesystem(default_dom, options.ip,
                                           virt=options.virt)
        if status != PASS:
            logger.error("Unable to define domain %s using DefineSystem()", \
                                                                 default_dom)
            return FAIL

        rc, cs = get_cs_instance(default_dom, options.ip, options.virt)
        if rc != 0:
            logger.error("GetInstance failed")
            undefine_test_domain(default_dom, options.ip)
            return FAIL

        # try to suspend
        cs.RequestStateChange( \
            RequestedState=pywbem.cim_types.Uint16(SUSPEND_STATE), \
            TimeoutPeriod=pywbem.cim_types.CIMDateTime(TIME))

    except pywbem.CIMError, (err_no, desc):
        if err_no == exp_rc and desc.find(exp_desc) >= 0:
            logger.info("Got expected exception where ")
            logger.info("Errno is '%s' ", exp_rc)
            logger.info("Error string is '%s'", exp_desc)
            undefine_test_domain(default_dom, options.ip, options.virt)
            return PASS
        logger.error("Unexpected RC: %s & Desc. %s", err_no, desc)
        undefine_test_domain(default_dom, options.ip, options.virt)
        return FAIL

    logger.error("Expected Defined -> Suspended state transition to fail")
    undefine_test_domain(default_dom, options.ip, options.virt)
    return FAIL

if __name__ == "__main__":
    sys.exit(main())
