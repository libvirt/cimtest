#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
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

# The following test case is used to verify the profiles supported
# by the VSM providers. 
#  
#                                          Date : 24-10-2007 
import sys
import pywbem
from XenKvmLib import enumclass
from XenKvmLib.classes import get_typed_class
from CimTest import Globals
from CimTest.Globals import do_main, logger
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

@do_main(sup_types)
def main():
    options = main.options

    explist = [['CIM:DSP1042-SystemVirtualization-1.0.0', 2,
                'System Virtualization', '1.0.0'],
               ['CIM:DSP1057-VirtualSystem-1.0.0a', 2,
                'Virtual System Profile', '1.0.0a']]
    cn = 'RegisteredProfile'

    status = PASS
    prev_namespace = Globals.CIM_NS
    Globals.CIM_NS = 'root/interop'

    try: 
        key_list = ["InstanceID"]
        proflist = enumclass.enumerate(options.ip, cn, key_list, options.virt)
    except Exception, detail:
        logger.error(Globals.CIM_ERROR_ENUMERATE, get_typed_class(options.virt,
                     cn))
        logger.error("Exception: %s", detail)
        status = FAIL
        Globals.CIM_NS = prev_namespace
        return status
    
    Globals.CIM_NS = prev_namespace

    checklist = [[x.InstanceID, x.RegisteredOrganization, 
                  x.RegisteredName, x.RegisteredVersion] for x in proflist]
    for exp_prof in explist:
        if exp_prof in checklist:
            logger.info("Profile %s found" % exp_prof[0])
        else:
            logger.error("Profile %s is not found" % exp_prof[0])
            status = FAIL
            break

    if status == PASS:
        logger.info("Properties check for %s passed" % cn)
    else:
        logger.error("Properties check for %s failed" % cn)
    return status

if __name__ == "__main__":
    sys.exit(main())
