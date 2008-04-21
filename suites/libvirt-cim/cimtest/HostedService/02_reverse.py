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
from XenKvmLib import hostsystem
from XenKvmLib.classes import get_typed_class
from CimTest import Globals
from CimTest.Globals import do_main
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL, XFAIL

sup_types = ['Xen', 'XenFV', 'KVM']

@do_main(sup_types)
def main():
    options = main.options
    try:
        host_sys = hostsystem.enumerate(options.ip, options.virt)[0]
    except Exception:
        logger.error(Globals.CIM_ERROR_ENUMERATE % host_sys.CreationClassName)
        return FAIL
    servicelist = {"ResourcePoolConfigurationService" : "RPCS", 
                   "VirtualSystemManagementService" : "Management Service",
                   "VirtualSystemMigrationService" : "MigrationService"}
    
    for k, v in servicelist.iteritems():
        try:
            assoc_host = assoc.AssociatorNames(options.ip, 
                                               "HostedService",
                                               k,
                                               options.virt,
                                               Name = v,
                                               CreationClassName = get_typed_class(options.virt, k),
                                               SystemCreationClassName = host_sys.CreationClassName,
                                               SystemName = host_sys.Name)
        except Exception:
            logger.error(Globals.CIM_ERROR_ASSOCIATORNAMES % item)
            return FAIL
        
        if len(assoc_host) != 1:
            logger.error("Too many hosts error")
            return FAIL

        ccn = assoc_host[0].keybindings['CreationClassName']
        name = assoc_host[0].keybindings['Name']
        
        if ccn != get_typed_class(options.virt, "HostSystem"):
            logger.error("CreationClassName Error")
            return FAIL
        elif name != host_sys.Name:
            logger.error("CCN Error")
            return FAIL
     
        
if __name__ == "__main__":
    sys.exit(main())
