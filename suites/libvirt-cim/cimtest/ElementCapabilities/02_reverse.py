#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
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

import sys
from VirtLib import utils
from VirtLib import live
from XenKvmLib import assoc
from XenKvmLib import hostsystem
from XenKvmLib import vsms
from XenKvmLib.classes import get_typed_class 
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE, CIM_ERROR_ASSOCIATORNAMES
from CimTest.Globals import do_main
from CimTest.ReturnCodes import PASS, FAIL, SKIP

sup_types = ['Xen', 'XenFV', 'KVM']

def call_assoc(ip, cn, id, virt="Xen"):
    status = PASS
    ec_ele = []
    try:
        ec_ele = assoc.AssociatorNames(ip,
                                       "ElementCapabilities",
                                       cn,
                                       virt, 
                                       InstanceID = id)
    except Exception:
        logger.error(CIM_ERROR_ASSOCIATORNAMES,
                     'ElementCapabilities')
        status = FAIL

    return status, ec_ele 

def filter(list, cn, exp_result):
    new_list = assoc.filter_by_result_class(list, cn)
    if len(new_list) != exp_result:
        logger.error("Expected %d host, got %d" % (exp_result, len(new_list)))
        return FAIL, new_list
    return PASS, new_list

def verify_host(inst_list, ip, virt="Xen"):
    hs = get_typed_class(virt, 'HostSystem')
    status, list = filter(inst_list, hs, 1) 
    if status != PASS:
        return status

    inst = list[0]
    try:
        host_sys = hostsystem.enumerate(ip, virt)[0]
    except Exception:
        logger.error(CIM_ERROR_ENUMERATE, 'HostSystem')
        return FAIL

    creationclassname = inst.keybindings['CreationClassName']
    name = inst.keybindings['Name']

    if creationclassname != host_sys.CreationClassName:
        logger.error("CreationClassName doesn't match")
        return FAIL
    elif name != host_sys.Name:
        logger.error("Name doesn't match")
        return FAIL

    return PASS

def verify_service(inst_list, ip, virt):
    service = get_typed_class(virt, "VirtualSystemManagementService")
    status, list = filter(inst_list, service, 1) 
    if status != PASS:
        return status

    inst = list[0]
    try:
        service = vsms.enumerate_instances(ip, virt)[0]
    except Exception:
        logger.error(CIM_ERROR_ENUMERATE, 
                     'VirtualSystemManagementService')
        return FAIL

    creationclassname = inst.keybindings['CreationClassName']
    name = inst.keybindings['Name']

    if creationclassname != service['CreationClassName']:
        logger.error("CreationClassName doesn't match")
        return FAIL
    elif name != service['Name']:
        logger.error("InstanceID doesn't match")
        return FAIL

    return PASS

@do_main(sup_types)
def main():
    options = main.options
    
    cap_list = {"VirtualSystemManagementCapabilities" : "ManagementCapabilities",
                "VirtualSystemMigrationCapabilities" : "MigrationCapabilities"}
    import pdb
    #pdb.set_trace()                
    for k, v in cap_list.iteritems():
        status, ec_ele = call_assoc(options.ip, k, v, options.virt)
        if status != PASS:
            return
        
        status = verify_host(ec_ele, options.ip, options.virt)
        if status != PASS:
            return status 
   
        if v == 'ManagementCapabilities':
            status = verify_service(ec_ele, options.ip, options.virt)
            if status != PASS:
                return status 

    cs = live.domain_list(options.ip, options.virt)
    for system in cs:
        status, elec_cs = call_assoc(options.ip, 
                                     "EnabledLogicalElementCapabilities", 
                                     system,
                                     options.virt)
        if status != PASS:
            return

        if len(elec_cs) < 1:
            logger.error("No ELEC instances returned")
            return FAIL

        if elec_cs[0].keybindings['CreationClassName'] != get_typed_class(options.virt, "ComputerSystem"):
            logger.error("Excpeted CreationClassName %s, got %s" %
                         ("ComputerSystem", 
                          elec_cs[0].keybindings['CreationClassName']))
            return FAIL
        elif elec_cs[0].keybindings['Name'] != system:
            logger.error("ElementCapabilities association Name error")
            return FAIL

    return PASS

if __name__ == "__main__":
    sys.exit(main())
