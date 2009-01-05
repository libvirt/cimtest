#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
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

# This test case defines a guest using DefineSystem().  The guest is then
# started (put in the "Active" state) using RequestStateChange(). 

# Steps:
#  1. Define a guest using DefineSystem().
#  2. Get the CIM instance of the guest created using DefineSystem().
#  3. Start the guest using RequestStateChange().
#  4. Get the CIM instance of the guest again - should have different values
#     for its attributes based on the state change.
#  5. Verify the instance attributes are correct after the state change. 
#

import sys
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.vxml import get_class

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

default_dom = 'cs_test_domain'

@do_main(sup_types)
def main():
    options = main.options
    server = options.ip
    virt = options.virt
    status = FAIL

    try:
        cxml = get_class(virt)(default_dom)
        ret = cxml.cim_define(server)
        if not ret:
            raise Exception("Failed to define the guest: %s" % default_dom)

        status = cxml.cim_start(server)
        if status != PASS:
            action_failed = True
            raise Exception("Unable start dom '%s'" % default_dom)

    except Exception, detail:
        logger.error("Exception: %s", detail)
        status = FAIL

    cxml.cim_destroy(server)
    cxml.undefine(server)

    return status

if __name__ == "__main__":
    sys.exit(main())
    
