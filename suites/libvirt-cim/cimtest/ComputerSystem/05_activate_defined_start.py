#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Veerendra Chandrappa <vechandr@in.ibm.com>
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
# has a value of "2" when the VS is moved from defined to activate state.
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
#						Date  : 17-10-2007

import sys
from XenKvmLib import computersystem
from XenKvmLib import vxml
from VirtLib import utils
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from XenKvmLib.common_util import call_request_state_change
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
test_dom = "DomST1"
mem = 128 # MB
bug_no  = "00002"
START_STATE = 3 
FINAL_STATE = 2
REQUESTED_STATE = FINAL_STATE 
TIME = "00000000000000.000000:000"

@do_main(sup_types)
def main():
    options = main.options
    status = FAIL

    cxml = vxml.get_class(options.virt)(test_dom, mem) 

#Define a VS
    try:
        ret = cxml.define(options.ip)
        if not ret :
            logger.error("ERROR: VS %s was not defined" % test_dom)
            return status 

        cs = computersystem.get_cs_class(options.virt)(options.ip, test_dom)
        if cs.Name == test_dom:
            from_State =  cs.EnabledState
        else:
            logger.error("ERROR: VS %s is not available" % test_dom)
            return status

    except Exception, detail:
        logger.error("Exception: %s" % detail)
        cxml.undefine(options.ip)
        return status
        
#Change the state of the  VS to Start
    rc = call_request_state_change(test_dom, options.ip, REQUESTED_STATE,
                                   TIME, options.virt)
    if rc != 0:
        logger.error("Unable start dom %s using RequestedStateChange()", test_dom)
        cxml.undefine(options.ip)
        return status

#Get the value of the EnabledState property and RequestedState property.
    try:
        cs = computersystem.get_cs_class(options.virt)(options.ip, test_dom)
        if cs.Name == test_dom:
            to_RequestedState = cs.RequestedState
            enabledState = cs.EnabledState
        else: 
            logger.error("VS %s is not found" % test_dom)
            return status 
# Success: 
# if  
# From state == 3
# To state == 2
# Enabled_state == RequestedState

        if from_State == START_STATE and \
           to_RequestedState == FINAL_STATE and \
           enabledState == to_RequestedState:
            status = PASS
        else:
            logger.error("ERROR: VS %s transition from Defined State to Activate state\
 was not Successful" % test_dom)
            status = XFAIL_RC(bug_no)
    except Exception, detail:
        logger.error("Exception: %s" % detail)

    cxml.destroy(options.ip)
    cxml.undefine(options.ip)
    return status
if __name__ == "__main__":
    sys.exit(main())
