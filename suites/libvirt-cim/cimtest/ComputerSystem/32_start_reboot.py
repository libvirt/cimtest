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
# Date: 03-03-2008

import sys
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC
from XenKvmLib.vxml import get_class

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']

bug_libvirt     = "00005"
default_dom = 'cs_test_domain'

@do_main(sup_types)
def main():
    options = main.options
    status = FAIL
    server = options.ip
    virt   = options.virt

    action_failed = False
    try:
        # define the vs
        cxml = get_class(virt)(default_dom)
        ret = cxml.cim_define(server)
        if not ret:
            raise Exception("Failed to define the guest: %s" % default_dom)

        status = cxml.cim_start(server)
        if status != PASS:
            raise Exception("Unable start dom '%s'" % default_dom)

        status = cxml.cim_reboot(server)
        if status != PASS:
            action_failed = True
            raise Exception("Unable reboot dom '%s'" % default_dom)

    except Exception, detail:
        logger.error("Exception: %s", detail)
        status = FAIL

    cxml.cim_destroy(server)
    cxml.undefine(server)

    if action_failed:
        if virt == "KVM" or virt == "LXC":
            return XFAIL_RC(bug_libvirt)

    return status

if __name__ == "__main__":
    sys.exit(main())
