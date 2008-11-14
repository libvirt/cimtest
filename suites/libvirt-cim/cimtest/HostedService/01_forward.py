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
from sets import Set
from VirtLib import utils
from XenKvmLib import assoc
from XenKvmLib import enumclass
from XenKvmLib.classes import get_typed_class
from CimTest import Globals
from XenKvmLib.const import do_main
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.common_util import get_host_info
from XenKvmLib.const import get_provider_version

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']
libvirtcim_hr_crs_changes = 695

@do_main(sup_types)
def main():
    options = main.options
    virt = options.virt
    server = options.ip
    try:
        status, host_inst = get_host_info(server, virt)
        if status != PASS:
            logger.error("Failed to get host info.")
            return status

        host_ccn = host_inst.CreationClassName
        host_name = host_inst.Name

        an = get_typed_class(virt, "HostedService")
        service = assoc.AssociatorNames(server,
                                        an, host_ccn,
                                        CreationClassName = host_ccn,
                                        Name = host_name)

    except Exception, deatils:
        logger.error(Globals.CIM_ERROR_ASSOCIATORNAMES % host_name)
        logger.error("Exception: details %s", details)
        return FAIL
    
    if service == None:
        logger.error("No association return")
        return FAIL

    val_serv = [get_typed_class(virt, "ResourcePoolConfigurationService"),
                get_typed_class(virt, "VirtualSystemManagementService"),
                get_typed_class(virt, "VirtualSystemMigrationService")]

    # This check is required for libivirt-cim providers which do not have 
    # CRS changes in it and the CRS provider is available with revision >= 695.
    cim_rev, changeset = get_provider_version(virt, server) 
    if cim_rev >= libvirtcim_hr_crs_changes:
        val_serv.append(get_typed_class(virt, "ConsoleRedirectionService"))

    val_serv = Set(val_serv)

    ccn_list = []
    for item in service:
        ccn_list.append(item.keybindings["CreationClassName"])

    ccn_list = Set(ccn_list) 
 
    if len((val_serv) - (ccn_list)) != 0:
        logger.error("Mismatching services values")
        logger.error("'%s' returned %d, expected %d", 
                     an, len(ccn_list), len(val_serv))
        return FAIL

    return PASS 
if __name__ == "__main__":
    sys.exit(main())
