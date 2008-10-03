#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
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
from VirtLib import utils
from XenKvmLib import assoc
from XenKvmLib import enumclass
from XenKvmLib.classes import get_typed_class
from CimTest import Globals
from XenKvmLib.const import do_main
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL, XFAIL
from XenKvmLib.common_util import get_host_info

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']

@do_main(sup_types)
def main():
    options = main.options
    virt = options.virt
    
    servicelist = {"ResourcePoolConfigurationService" : "RPCS", 
                   "VirtualSystemManagementService" : "Management Service",
                   "VirtualSystemMigrationService" : "MigrationService"}

    status, host_name, host_ccn = get_host_info(options.ip, virt)
    if status != PASS:
        logger.error("Failed to get host info.")
        return status
    
    an = get_typed_class(virt, "HostedService")
    for k, v in servicelist.iteritems():
        cn = get_typed_class(virt, k)
        try:
            assoc_host = assoc.AssociatorNames(options.ip, an, cn, 
                                               Name = v,
                                               CreationClassName = cn,
                                               SystemCreationClassName = host_ccn,
                                               SystemName = host_name)
        except Exception:
            logger.error(Globals.CIM_ERROR_ASSOCIATORNAMES, an)
            return FAIL
        
        if len(assoc_host) != 1:
            logger.error("Too many hosts")
            return FAIL

        ccn = assoc_host[0].keybindings['CreationClassName']
        name = assoc_host[0].keybindings['Name']
        
        if ccn != host_ccn:
            logger.error("CreationClassName Error")
            return FAIL

        elif name != host_name:
            logger.error("CCN Error")
            return FAIL
     
        
if __name__ == "__main__":
    sys.exit(main())
