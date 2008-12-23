#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Veerendra Chandrappa <vechandr@in.ibm.com>
#    Zhengang Li <lizg@cn.ibm.com>
#    Deepti B. kalakeri <deeptik@linux.vnet.ibm.com>
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

# This test case checks state of the VS is in enabled state after 
# defining and starting the  VS.
# By verifying the properties of EnabledState = 2 of the VS.
#                               
#                                                             10-Oct-2007

import sys
from XenKvmLib.vxml import get_class 
from CimTest.Globals import logger 
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
test_dom = "domguest"

@do_main(sup_types)
def main():
    options = main.options
    status = FAIL

    cxml = get_class(options.virt)(test_dom)
    try:
        ret = cxml.cim_define(options.ip)
        if not ret:
            logger.error("Unable to define %s" % test_dom)
            return FAIL

        status = cxml.cim_start(options.ip)
        if status != PASS:
            logger.error("Failed to Start the dom: %s" % test_dom)
            logger.error("Property values not set properly for %s", test_dom) 
    
    except Exception, detail:
        logger.error("Exception: %s", detail)
        status = FAIL

    cxml.destroy(options.ip)
    cxml.undefine(options.ip)

    return status

if __name__ == "__main__":
    sys.exit(main())

