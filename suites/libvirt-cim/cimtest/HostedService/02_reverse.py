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
from XenKvmLib.const import get_provider_version

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']
libvirtcim_hr_crs_changes = 695

@do_main(sup_types)
def main():
    options = main.options
    server = options.ip
    virt = options.virt
    
    servicelist = {"ResourcePoolConfigurationService" : "RPCS", 
                   "VirtualSystemManagementService" : "Management Service",
                   "VirtualSystemMigrationService" : "MigrationService"}

    # This check is required for libivirt-cim providers which do not have 
    # CRS changes in it and the CRS provider is available with revision >= 695.
    cim_rev, changeset = get_provider_version(virt, server) 
    if cim_rev >= libvirtcim_hr_crs_changes:   
        servicelist['ConsoleRedirectionService'] =  "ConsoleRedirectionService"

    status, host_name, host_ccn = get_host_info(server, virt)
    if status != PASS:
        logger.error("Failed to get host info.")
        return status
    
    an = get_typed_class(virt, "HostedService")
    for k, v in servicelist.iteritems():
        cn = get_typed_class(virt, k)
        try:
            assoc_host = assoc.AssociatorNames(server, an, cn, 
                                               Name = v,
                                               CreationClassName = cn,
                                               SystemCreationClassName = host_ccn,
                                               SystemName = host_name)
        except Exception:
            logger.error(Globals.CIM_ERROR_ASSOCIATORNAMES, an)
            return FAIL
        
        if len(assoc_host) != 1:
            logger.error("'%s' association failed", an)
            return FAIL

        ccn = assoc_host[0].keybindings['CreationClassName']
        name = assoc_host[0].keybindings['Name']
        
        if ccn != host_ccn:
            logger.error("CreationClassName Error")
            return FAIL

        if name != host_name:
            logger.error("CCN Error")
            return FAIL
    return PASS
     
        
if __name__ == "__main__":
    sys.exit(main())
