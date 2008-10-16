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
from sets import Set
from XenKvmLib import enumclass
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE
from XenKvmLib.const import do_main
from XenKvmLib.classes import get_typed_class
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.common_util import print_field_error

sup_types=['Xen', 'KVM', 'XenFV', 'LXC']

@do_main(sup_types)
def main():
    options = main.options
    server  = options.ip
    virt    = options.virt
    cn      = get_typed_class(virt, 'VirtualSystemManagementCapabilities')

    # Methods which are considered as synchronous
    # where 1 = ADD_RESOURCES , 2 = DEFINE_SYSTEM , 3 = DESTROY_SYSTEM,
    # 4 = DESTROY_SYS_CONFIG, 5 = MOD_RESOURCE_SETTINGS,
    # 6 =  MOD_SYS_SETTINGS,  7 = RM_RESOURCES
    sync_method_val = Set([ 1L, 2L, 3L, 5L, 6L, 7L ])

    try:
        vsmc = enumclass.EnumInstances(server, cn)
    except Exception:
       logger.error(CIM_ERROR_ENUMERATE, cn)
       return FAIL 

    try:
        if len(vsmc) != 1:
            logger.error("'%s' returned '%d' instance, excepted only 1", 
                         cn, len(vsmc))
            return FAIL
 
        if vsmc[0].InstanceID != "ManagementCapabilities":
            print_field_error('InstanceID', vsmc[0].InstanceID,
                              'ManagementCapabilities')
            return FAIL

        vsmc_sync_val = Set(vsmc[0].SynchronousMethodsSupported)
        if len(vsmc_sync_val - sync_method_val) != 0:
            print_field_error('SynchronousMethodsSupported', vsmc_sync_val, 
                               sync_method_val)
            return FAIL

    except Exception, details:
        logger.error("Exception: details %s", details)
        return FAIL

    return PASS

if __name__ == "__main__":
    sys.exit(main())
