#!/usr/bin/python
#
# Copyright 2011 IBM Corp.
#
# Authors:
#    Sharad Mishra <snmishra@us.ibm.com>
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
from XenKvmLib import enumclass
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger
from CimTest.ReturnCodes import XFAIL

SUPPORTED_TYPES = ['Xen', 'KVM', 'XenFV']

@do_main(SUPPORTED_TYPES)
def main():
    options = main.options 

    cs_class = get_typed_class(options.virt, 'SwitchService')
    try:
        cs = enumclass.EnumInstances(options.ip, cs_class)
        print "Please check if this is the expected result ---"
        for name in cs:
            if name.IsVSISupported:
                print "*** VSI supported ***"
            else:
                print "*** VSI NOT supported ***"
    except Exception, detail:
        logger.error("Exception: %s", detail)

    return XFAIL

if __name__ == "__main__":
    sys.exit(main())
