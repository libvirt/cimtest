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
from XenKvmLib import vxml
from VirtLib import utils
from XenKvmLib.test_doms import destroy_and_undefine_all
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from XenKvmLib.common_util import call_request_state_change, \
poll_for_state_change
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV']
test_dom = "DomST1"
mem = 128 # MB
START_STATE = 2 
FINAL_STATE = 9
TIME = "00000000000000.000000:000"

@do_main(sup_types)
def main():
    options = main.options
    status = FAIL
    server = options.ip
    virt = options.virt

    destroy_and_undefine_all(server)
    
    cxml = vxml.get_class(virt)(test_dom, mem)

    #Create VS
    try:
        ret = cxml.create(server)
        if not ret:
            logger.error("VS '%s' was not created" % test_dom)
            return status
    except Exception, detail:
        logger.error("Exception variable: %s" % detail)
        return status
 
    status, dom_cs = poll_for_state_change(server, virt, test_dom, 
                                           START_STATE)

    if status != PASS:
        cxml.destroy(server)
        return status

    from_State = dom_cs.EnabledState
 
    #Suspend the VS
    status = call_request_state_change(test_dom, server, FINAL_STATE,
                                       TIME, virt)
    if status != PASS:
        logger.error("Unable to suspend dom '%s' using RequestedStateChange()", 
                      test_dom)
        cxml.destroy(server)
        return status

    #Polling for the value of EnabledState to be set to 9.
    #We need to wait for the EnabledState to be set appropriately since
    #it does not get set immediatley to value of 9 when suspended.
    status, dom_cs = poll_for_state_change(server, virt, test_dom, 
                                           FINAL_STATE, timeout=40)

    if status != PASS:
        cxml.destroy(server)
        return status

    enabledState = dom_cs.EnabledState
    to_RequestedState = dom_cs.RequestedState

    # Success: 
    # if  
    # From state == 2
    # To state == 9
    # Enabled_state == RequestedState

    if from_State == START_STATE and \
        to_RequestedState == FINAL_STATE and \
        to_RequestedState == enabledState:
        status = PASS
    else:
        logger.error("VS '%s' transition from Activate State to Suspend State" 
                     " was not Successful" % test_dom)
        status = FAIL

    cxml.destroy(server)
    
    return status
if __name__ == "__main__":
    sys.exit(main())
