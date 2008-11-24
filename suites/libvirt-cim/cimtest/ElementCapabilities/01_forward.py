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
from XenKvmLib.xm_virt_util import domain_list
from XenKvmLib import vxml
from XenKvmLib import assoc
from XenKvmLib import enumclass
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger, CIM_ERROR_ASSOCIATORNAMES
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from XenKvmLib.enumclass import EnumInstances
from XenKvmLib.common_util import get_host_info
from XenKvmLib.const import get_provider_version

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']
test_dom  = "dom_elecap"
libvirtcim_crsc_changes = 723 

def append_to_list(server, virt, poolname, valid_elc_id):
    poolname = get_typed_class(virt, poolname)
    pool_list = EnumInstances(server, poolname) 
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
        valid_elc_id = append_to_list(server, virt, "GraphicsPool", valid_elc_id)
        valid_elc_id = append_to_list(server, virt, "InputPool", valid_elc_id)

    except Exception, details:
        logger.error("Exception: In fn set_pool_info(): %s", details)
        return FAIL, valid_elc_id

    return PASS, valid_elc_id


@do_main(sup_types)
def main():
    options = main.options
    server = options.ip
    virt = options.virt

    status, host_inst = get_host_info(server, virt)
    if status != PASS:
        logger.error("Failed to get host info")
        return status

    host_ccn = host_inst.CreationClassName
    host_name = host_inst.Name

    try:
        an = get_typed_class(virt, "ElementCapabilities")
        elc = assoc.AssociatorNames(server,
                                    an, host_ccn,
                                    Name = host_name,
                                    CreationClassName = host_ccn)
    except Exception:
        logger.error(CIM_ERROR_ASSOCIATORNAMES, an)
        return FAIL

    valid_elc_name = [get_typed_class(virt, "VirtualSystemManagementCapabilities"),
                      get_typed_class(virt, "VirtualSystemMigrationCapabilities")]

    valid_elc_id = ["ManagementCapabilities", 
                    "MigrationCapabilities"]

    cim_rev, changeset = get_provider_version(virt, server)
    if cim_rev  >= libvirtcim_crsc_changes:
        crsc =  get_typed_class(virt, "ConsoleRedirectionServiceCapabilities")
        valid_elc_name.append(crsc)
        valid_elc_id.append("ConsoleRedirectionCapabilities")

    valid_elc_name.append(get_typed_class(virt, "AllocationCapabilities"))
    status, valid_elc_id = set_pool_info(server, virt, valid_elc_id)
    if status != PASS:
        return status

    if len(elc) == 0:
        logger.error("'%s' association failed, expected at least one instance",
                     an)
        return FAIL

    for i in elc:
        if i.classname not in valid_elc_name:
            logger.error("'%s' association classname error", an)
            return FAIL
        if i['InstanceID'] not in valid_elc_id:
            logger.error("'%s' association InstanceID error ", an)
            return FAIL

    virtxml = vxml.get_class(virt)
    cxml = virtxml(test_dom)
    ret = cxml.cim_define(server)
    if not ret:
        logger.error("Failed to define the dom: %s", test_dom)
        return FAIL

    cs = domain_list(server, virt)
    ccn  = get_typed_class(virt, "ComputerSystem")
    for system in cs:  
        try:
	    elec = assoc.AssociatorNames(server, an, ccn, Name = system, 
                                         CreationClassName = ccn)
  	except Exception:
            logger.error(CIM_ERROR_ASSOCIATORNAMES % system)
            cxml.undefine(server)
            return FAIL     

        cn = get_typed_class(virt, "EnabledLogicalElementCapabilities") 
        if elec[0].classname != cn:
            cxml.undefine(server)
            logger.error("'%s' association classname error", an)
            return FAIL

        if elec[0].keybindings['InstanceID'] != system:
            logger.error("ElementCapabilities association InstanceID error")
            cxml.undefine(server)
            logger.error("'%s' association InstanceID error", an)
            return FAIL

    cxml.undefine(server)
    return PASS

if __name__ == "__main__":
    sys.exit(main())
