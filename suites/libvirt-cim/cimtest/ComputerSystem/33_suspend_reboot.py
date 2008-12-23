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
# has a value of 9 when the VS is moved from active to suspend state
# and when rebooted the value of RequestedState should be 10.
#
# List of Valid state values (Refer to VSP spec doc Table 2 for more)
# ---------------------------------
# State             |   Values
# ---------------------------------
# Defined           |     3
# Active            |     2
# Suspended         |     6
# Rebooted          |    10
#
#                                                   Date: 06-03-2008

import sys
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC
from XenKvmLib.vxml import get_class

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']

bug_libvirt     = "00012"

default_dom = 'test_domain'

@do_main(sup_types)
def main():
    options = main.options
    status = FAIL
    server = options.ip
    virt   = options.virt

    tc_scen = ['Start', 'Suspend', 'Reboot'] 

    action_passed = PASS 
    try:
        # define the vs
        cxml = get_class(options.virt)(default_dom)
        ret = cxml.cim_define(server)
        if not ret:
            raise Exception("Failed to define the guest: %s" % default_dom)

        # start, suspend and reboot
        for action in tc_scen:
            if action == "Start":
                status = cxml.cim_start(server)
            elif action == "Suspend":
                status = cxml.cim_suspend(server)
            elif action == "Reboot":
                status = cxml.cim_reboot(server)
            else:
                raise Exception("Unexpected state change: %s" % action)

            if status != PASS:
                action_passed = FAIL
                raise Exception("Unable %s dom '%s'" % (action, default_dom))

    except Exception, detail:
        logger.error("Exception: %s", detail)
        status = FAIL

    cxml.cim_destroy(server)
    cxml.undefine(server)

    if action_passed == FAIL:
        return XFAIL_RC(bug_libvirt)

    return status

if __name__ == "__main__":
    sys.exit(main())
