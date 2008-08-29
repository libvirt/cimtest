#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
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
from VirtLib import live
from XenKvmLib import assoc
from XenKvmLib import enumclass
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger, CIM_ERROR_ASSOCIATORNAMES, \
                            CIM_ERROR_ENUMERATE
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from XenKvmLib.enumclass import enumerate

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']

def append_to_list(server, virt, poolname, valid_elc_id):
    keys_list = ['InstanceID']
    pool_list = enumerate(server, poolname, keys_list, virt) 
    if len(pool_list) > 0:
        for pool in pool_list:
            valid_elc_id.append(pool.InstanceID)
    return valid_elc_id

def set_pool_info(server, virt, valid_elc_id):
    try:
        valid_elc_id = append_to_list(server, virt, "DiskPool", valid_elc_id)
        valid_elc_id = append_to_list(server, virt, "MemoryPool", valid_elc_id)
        valid_elc_id = append_to_list(server, virt, "ProcessorPool", valid_elc_id)
        valid_elc_id = append_to_list(server, virt, "NetworkPool", valid_elc_id)
    except Exception, details:
        logger.error("Exception: In fn set_pool_info(): %s", details)
        return FAIL, valid_elc_id

    return PASS, valid_elc_id


@do_main(sup_types)
def main():
    options = main.options
    server = options.ip
    virt = options.virt
    keys = ['Name', 'CreationClassName']
    try:
        host_sys = enumclass.enumerate(server, 'HostSystem', keys, virt)[0]
    except Exception:
        logger.error(CIM_ERROR_ENUMERATE, get_typed_class(virt, 'HostSystem'))
        return FAIL

    try:
        elc = assoc.AssociatorNames(server,
                                     "ElementCapabilities",
                                     "HostSystem", 
                                     virt,
                                     Name = host_sys.Name,
                                     CreationClassName = host_sys.CreationClassName)
    except Exception:
        logger.error(CIM_ERROR_ASSOCIATORNAMES % host_sys.Name)
        return FAIL


    valid_elc_name = [get_typed_class(virt, "VirtualSystemManagementCapabilities"),
                      get_typed_class(virt, "VirtualSystemMigrationCapabilities")]

    valid_elc_id = ["ManagementCapabilities", 
                    "MigrationCapabilities"]

    valid_elc_name.append(get_typed_class(virt, "AllocationCapabilities"))
    status, valid_elc_id = set_pool_info(server, virt, valid_elc_id)
    if status != PASS:
        return status

    if len(elc) == 0:
        logger.error("ElementCapabilities association failed, excepted at least one instance")
        return FAIL

    for i in elc:
        if i.classname not in valid_elc_name:
            logger.error("ElementCapabilities association classname error")
            return FAIL
        if i['InstanceID'] not in valid_elc_id:
            logger.error("ElementCapabilities association InstanceID error ")
            return FAIL

    cs = live.domain_list(server, virt)
    ccn  = get_typed_class(virt, "ComputerSystem")
    for system in cs:  
        try:
	    elec = assoc.AssociatorNames(server,
                                         "ElementCapabilities",
                                         "ComputerSystem",
                                         virt,
                                         Name = system,
                                         CreationClassName = ccn)
  	except Exception:
            logger.error(CIM_ERROR_ASSOCIATORNAMES % system)
            return FAIL     
        cn = get_typed_class(virt, "EnabledLogicalElementCapabilities") 
        if elec[0].classname != cn:
	    logger.error("ElementCapabilities association classname error")
            return FAIL
        elif elec[0].keybindings['InstanceID'] != system:
            logger.error("ElementCapabilities association InstanceID error")
            return FAIL

    return PASS

if __name__ == "__main__":
    sys.exit(main())
