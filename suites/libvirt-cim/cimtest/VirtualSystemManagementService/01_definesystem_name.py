#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
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

import sys
from XenKvmLib.const import do_main
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.vxml import get_class

SUPPORTED_TYPES = ['Xen', 'KVM', 'XenFV', 'LXC']
default_dom = 'test_domain'

@do_main(SUPPORTED_TYPES)
def main():
    options = main.options

    cxml = get_class(options.virt)(default_dom)

    ret = cxml.cim_define(options.ip)
    if not ret:
        logger.error("Unable to define %s" % default_dom)
        return FAIL

    status = cxml.cim_start(options.ip)
    if status != PASS:
        logger.error("Failed to start the defined domain: %s" % default_dom) 

    cxml.cim_destroy(options.ip)
    cxml.undefine(options.ip)

    return status

if __name__ == "__main__":
    sys.exit(main())

