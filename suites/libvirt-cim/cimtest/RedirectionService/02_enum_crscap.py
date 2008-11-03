#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
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
# This test case is used to verify the ConsoleRedirectionServiceCapabilities
# properties in detail.
#
#                                               Date : 22-10-2008
#

import sys
from XenKvmLib.xm_virt_util import domain_list
from XenKvmLib.enumclass import EnumInstances
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE
from XenKvmLib.classes import get_typed_class
from XenKvmLib.const import do_main 
from CimTest.ReturnCodes import PASS, FAIL

SHAREMODESUPP = 3

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
@do_main(sup_types)
def main():
    virt = main.options.virt
    server = main.options.ip
    cname = 'ConsoleRedirectionServiceCapabilities'
    cap_name = 'ConsoleRedirectionCapabilities'
    classname = get_typed_class(virt, cname)
    try:
        crs = EnumInstances(server, classname)

        if len(crs) != 1:
            logger.error("'%s' returned %i records, expected 1", 
                         classname, len(crs))
            return FAIL

        crs_val = crs[0]
        if crs_val.InstanceID != cap_name:
            logger.error("InstanceID Mismatch")
            logger.error("Got '%s', Expected '%s'", crs_val.InstanceID, 
                         cap_name)
            return FAIL

        if crs_val.ElementName != cap_name:
            logger.error("ElementName Mismatch")
            logger.error("Got '%s', Expected '%s'", crs_val.ElementName, 
                         cap_name)
            return FAIL
         
        mode_supp =  crs_val.SharingModeSupported[0]
        if mode_supp != SHAREMODESUPP:
            logger.error("SharingModeSupported Mismatch")
            logger.error("Got '%s', Expected '%s'", mode_supp, SHAREMODESUPP)
            return FAIL

    except Exception, detail:
        logger.error(CIM_ERROR_ENUMERATE, classname)
        logger.error("Exception: %s", detail)
        return FAIL

    return PASS

if __name__ == "__main__":
    sys.exit(main())
