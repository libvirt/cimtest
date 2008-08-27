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
from CimTest.Globals import do_main
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL, XFAIL

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']

@do_main(sup_types)
def main():
    options = main.options
    keys = ['Name', 'CreationClassName']
    try:
        host_sys = enumclass.enumerate(options.ip, 'HostSystem', keys, options.virt)[0]
    except Exception:
        logger.error(Globals.CIM_ERROR_ENUMERATE % host_sys.name)
        return FAIL
    try:
        service = assoc.AssociatorNames(options.ip,
                                        "HostedService",
                                        "HostSystem",
                                        options.virt,
                                        CreationClassName = host_sys.CreationClassName,
                                        Name = host_sys.Name)
    except Exception:
        logger.error(Globals.CIM_ERROR_ASSOCIATORNAMES % host_sys.Name)
        return FAIL
    
    if service == None:
        logger.error("No association return")
        return FAIL

    valid_services = [get_typed_class(options.virt, "ResourcePoolConfigurationService"), 
                      get_typed_class(options.virt, "VirtualSystemManagementService"),
                      get_typed_class(options.virt, "VirtualSystemMigrationService")]
    for item in service:
        ccn = item.keybindings["CreationClassName"]
        if ccn not in valid_services:
            logger.error("HostedService association to associate HostSystem and %s is wrong " % ccn)
            return FAIL

                    
if __name__ == "__main__":
    sys.exit(main())
