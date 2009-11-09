#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
#
# Authors:
#    Kaitlin Rupert <karupert@us.ibm.com>
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
# has a value of enabled/disabled when the VS is moved from active state
# to a disabled state. 
#
# For providers older than 945, the guest will be rebooted. Otherwise, it will
# be destroyed and placed in the 'defined' state.
#
# Date: 08-07-2009

import sys
from CimTest.Globals import logger
from XenKvmLib.const import do_main, CIM_ENABLE, CIM_DISABLE, \
                            get_provider_version
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from XenKvmLib.vxml import get_class

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']

default_dom = 'cs_test_domain'

disable_change_rev = 945

@do_main(sup_types)
def main():
    options = main.options
    status = FAIL
    server = options.ip
    virt   = options.virt

    try:
        rev, changeset = get_provider_version(virt, server)
        if rev >= disable_change_rev: 
            exp_state = CIM_DISABLE
        else:
            if options.virt == "KVM":
                logger.info("cimtest's KVM guest imagedoesn't support reboot")
                return SKIP
            exp_state = CIM_ENABLE

        cxml = get_class(virt)(default_dom)
        ret = cxml.cim_define(server)
        if not ret:
            raise Exception("Failed to define the guest: %s" % default_dom)

        status = cxml.cim_start(server)
        if status != PASS:
            raise Exception("Unable start dom '%s'" % default_dom)

        status = cxml.cim_disable(server)
        if status != PASS:
            raise Exception("Unable disable dom '%s'" % default_dom)

        status = cxml.check_guest_state(server, exp_state)
        if status != PASS:
            raise Exception("%s not in expected state %d" % \
                            (default_dom, exp_state))

    except Exception, detail:
        logger.error("Exception: %s", detail)
        status = FAIL
  
    #Call destroy incase disable fails or for older provider
    #version where disable causes guest to be rebooted
    cxml.cim_destroy(server)
    cxml.undefine(server)

    return status

if __name__ == "__main__":
    sys.exit(main())
