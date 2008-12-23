#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
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

# This test case is used to verify the Virtual System State Transition
# information is captured in the RequestedState Property of the VS.
# The test is considered to be successful if 'Suspend' of the 'defined' domU
# is not possible
# Date: 14-12-2007

import sys
from XenKvmLib.vxml import get_class 
from CimTest.Globals import logger
from XenKvmLib.const import do_main 
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
test_dom = "domgst"

@do_main(sup_types)
def main():
    options = main.options

    cxml = get_class(options.virt)(test_dom)

    status = FAIL
    try:
        # define the vs
        ret = cxml.cim_define(options.ip)
        if not ret:
            raise Exception("Unable to define %s" % test_dom)

        # suspend the vs
        status = cxml.cim_suspend(options.ip)
        if status != PASS:
            logger.info("Suspending defined %s failed, as expected" % test_dom)
            status = PASS
        else:
            raise Exception("Suspending defined %s should have failed" % \
                            test_dom)

    except Exception, detail:
        logger.error("Error: %s" % detail)
        status = FAIL 

    cxml.undefine(options.ip)

    return status

if __name__ == "__main__":
    sys.exit(main())

