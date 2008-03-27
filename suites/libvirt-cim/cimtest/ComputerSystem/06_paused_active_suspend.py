#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
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

# This test case is used to verify the Virtual System State Transition,
# information related to this is captured in the RequestedState Property
# of the VS.
# The test is considered to be successful if RequestedState Property 
# has a value of "9" when the VS is moved from active to suspend state.
#
# List of Valid state values (Refer to VSP spec doc Table 2 for more)
# ---------------------------------
# State             |   Values
# ---------------------------------
# Defined           |     3
# Active            |     2
# Paused            |     9
# Suspended         |     6 
#
# 
#						Date  :18-10-2007

import sys
from time import sleep
from XenKvmLib import computersystem
from XenKvmLib import vxml
from VirtLib import utils
from XenKvmLib.test_doms import destroy_and_undefine_all
from CimTest.Globals import log_param, logger
from CimTest.Globals import do_main
from XenKvmLib.common_util import call_request_state_change
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC

sup_types = ['Xen', 'KVM', 'XenFV']
test_dom = "DomST1"
mem = 128 # MB
# Keeping the bug no for future reference
# bug_no_req_change_method = "90559"
bug_no_req_change_prop   = "85769"
START_STATE = 2 
FINAL_STATE = 9
REQUESTED_STATE = FINAL_STATE
TIME = "00000000000000.000000:000"

@do_main(sup_types)
def main():
    options = main.options
    status = FAIL
    log_param()
    
    cxml = vxml.get_class(options.virt)(test_dom, mem)

#Create VS
    try:
        ret = cxml.create(options.ip)
        if not ret:
            logger.error("ERROR: VS %s was not created" % test_dom)
            return status
        cs = computersystem.get_cs_class(options.virt)(options.ip, test_dom)
        if cs.Name == test_dom:
            from_State = cs.EnabledState
        else:
            logger.error("ERROR: VS %s not found" % test_dom)
            return status
    except Exception, detail:
        logger.error("Exception variable: %s" % detail)
        cxml.destroy(options.ip)
        cxml.undefine(options.ip)
        return status
 
#Suspend the VS
    rc = call_request_state_change(test_dom, options.ip, REQUESTED_STATE,
                                   TIME, options.virt)
    if rc != 0:
        logger.error("Unable to suspend dom %s using RequestedStateChange()", test_dom)
        cxml.destroy(options.ip)
        cxml.undefine(options.ip)
        return status
#Polling for the value of EnabledState to be set to 9.
#We need to wait for the EnabledState to be set appropriately since
#it does not get set immediatley to value of 9 when suspended.
    timeout = 10
    try:

        for i in range(1, (timeout + 1)):
            sleep(1)
            cs = computersystem.get_cs_class(options.virt)(options.ip, test_dom)
            if cs.Name == test_dom:
                to_RequestedState = cs.RequestedState
                enabledState =  cs.EnabledState
            else:
                logger.error("VS %s not found" % test_dom)
                return status 
            if enabledState == FINAL_STATE:
                status = PASS
                break

    except Exception, detail:
        logger.error("Exception variable: %s" % detail)
        return status

    if enabledState != FINAL_STATE:
        logger.error("EnabledState has %i instead of %i", enabledState, FINAL_STATE)
        logger.error("Try to increase the timeout and run the test again")

    if status != PASS:
        ret = cxml.destroy(options.ip)
        cxml.undefine(options.ip)
        return status

# Success: 
# if  
# From state == 9
# To state == 2
# Enabled_state == RequestedState

    if from_State == START_STATE and \
        to_RequestedState == FINAL_STATE and \
        enabledState == to_RequestedState:
        status = PASS
    else:
        logger.error("ERROR: VS %s transition from suspend State to Activate state \
 was not Successful" % test_dom)
# Replace the status with FAIL once the bug is fixed.
        status = XFAIL_RC(bug_no_req_change_prop)
    ret = cxml.destroy(options.ip)
    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())
