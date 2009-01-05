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
# state change from defined to paused fails
#
# Date: 05-03-2008
#

import sys
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.vxml import get_class

sup_types = ['Xen', 'XenFV', 'LXC', 'KVM']

default_dom   = 'test_domain'

@do_main(sup_types)
def main():
    options = main.options
    server = options.ip
    virt   = options.virt
    status = FAIL

    try:
        # define the vs
        cxml = get_class(options.virt)(default_dom)
        ret = cxml.cim_define(server)
        if not ret:
            raise Exception("Failed to define the guest: %s" % default_dom)

        status = cxml.cim_pause(server)
        if status != PASS:
            raise Exception("Unable pause dom '%s'" % default_dom)

    except Exception, details:
        logger.error("Exception: %s", details)
        status = FAIL

    if status != FAIL:
        logger.error("Expected Defined -> Paused state transition to fail")
        status = FAIL
    else:
        status = PASS 

    cxml.undefine(server)

    return status 

if __name__ == "__main__":
    sys.exit(main())
