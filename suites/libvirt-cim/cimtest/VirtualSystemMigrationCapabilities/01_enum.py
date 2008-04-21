#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Deepti B. Kalakeri<dkalaker@in.ibm.com>
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
from XenKvmLib import enumclass
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import CIM_ERROR_ENUMERATE, logger, do_main
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'XenFV', 'KVM']

def print_error(fieldname, ret_value, exp_value):
    logger.error("%s Mismatch", fieldname)
    logger.error("Returned %s instead of %s", ret_value, exp_value)

@do_main(sup_types)
def main():
    options = main.options

    # Expected values from the enumetation
    cn     = get_typed_class(options.virt, 'VirtualSystemMigrationCapabilities')
    instid = 'MigrationCapabilities'

    try:
        vsmc = enumclass.enumerate_inst(options.ip,
                                        "VirtualSystemMigrationCapabilities",
                                        options.virt)
    except Exception:
        logger.error(CIM_ERROR_ENUMERATE, cn)
        return FAIL
     
    if len(vsmc) != 1:
        logger.error("%s return %i instances, excepted only 1 instance", cn, len(vsmc))
        return FAIL
    verify_vsmc =  vsmc[0]
    if verify_vsmc.classname != cn:
        print_error('ClassName', verify_vsmc.classname, cn)
        return FAIL
    if verify_vsmc['InstanceID'] != instid:
        print_error('InstanceID', verify_vsmc['InstanceID'], instid)
        return FAIL
    return PASS

if __name__ == "__main__":
    sys.exit(main())
