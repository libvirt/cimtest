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
from CimTest.Globals import log_param, logger, CIM_ERROR_ENUMERATE, CIM_ERROR_ASSOCIATORNAMES
from CimTest.Globals import do_main
from CimTest.ReturnCodes import PASS, FAIL, SKIP

sup_types = ['xen']

def call_assoc(ip, cn, id):
    status = PASS
    ec_ele = []
    try:
        ec_ele = assoc.AssociatorNames(ip,
                                       "Xen_ElementCapabilities",
                                       cn, 
                                       InstanceID = id)
    except Exception:
        logger.error(CIM_ERROR_ASSOCIATORNAMES,
                     'Xen_ElementCapabilities')
        status = FAIL

    return status, ec_ele 

def filter(list, cn, exp_result):
    new_list = assoc.filter_by_result_class(list, cn)
    if len(new_list) != exp_result:
        logger.error("Expected %d host, got %d" % (exp_result, len(new_list)))
        return FAIL, new_list
    return PASS, new_list

def verify_host(inst_list, ip):
    status, list = filter(inst_list, 'Xen_HostSystem', 1) 
    if status != PASS:
        return status

    inst = list[0]
    try:
        host_sys = hostsystem.enumerate(ip)[0]
    except Exception:
        logger.error(CIM_ERROR_ENUMERATE, 'Xen_HostSystem')
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

def verify_service(inst_list, ip):
    status, list = filter(inst_list, 'Xen_VirtualSystemManagementService', 1) 
    if status != PASS:
        return status

    inst = list[0]
    try:
        service = vsms.enumerate_instances(ip)[0]
    except Exception:
        logger.error(CIM_ERROR_ENUMERATE, 
                     'Xen_VirtualSystemManagementService')
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
    log_param()
    
    cap_list = {"Xen_VirtualSystemManagementCapabilities" : "ManagementCapabilities",
                "Xen_VirtualSystemMigrationCapabilities" : "MigrationCapabilities"}
                
    for k, v in cap_list.iteritems():
        status, ec_ele = call_assoc(options.ip, k, v)
        if status != PASS:
            return

        status = verify_host(ec_ele, options.ip)
        if status != PASS:
            return status 
   
        if v == 'ManagementCapabilities':
            status = verify_service(ec_ele, options.ip)
            if status != PASS:
                return status 

    cs = live.domain_list(options.ip)
    for system in cs:
        status, elec_cs = call_assoc(options.ip, 
                                     "Xen_EnabledLogicalElementCapabilities", 
                                     system)
        if status != PASS:
            return

        if len(elec_cs) < 1:
            logger.error("No ELEC instances returned")
            return FAIL

        if elec_cs[0].keybindings['CreationClassName'] != "Xen_ComputerSystem":
            logger.error("Excpeted CreationClassName %s, got %s" %
                         ("Xen_ComputerSystem", 
                          elec_cs[0].keybindings['CreationClassName']))
            return FAIL
        elif elec_cs[0].keybindings['Name'] != system:
            logger.error("ElementCapabilities association Name error")
            return FAIL

    return PASS

if __name__ == "__main__":
    sys.exit(main())
