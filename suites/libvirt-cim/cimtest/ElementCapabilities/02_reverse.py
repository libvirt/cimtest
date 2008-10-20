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
from XenKvmLib import enumclass
from XenKvmLib import vxml
from XenKvmLib.classes import get_typed_class
from XenKvmLib.classes import get_class_basename
from XenKvmLib.common_util import get_host_info
from CimTest.Globals import logger, CIM_ERROR_GETINSTANCE, \
                            CIM_ERROR_ASSOCIATORNAMES
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from XenKvmLib.enumclass import GetInstance

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']
test_dom  = "dom_elecap"

def call_assoc(ip, cn, id, virt="Xen"):
    status = PASS
    ec_ele = []
    assoc_cn = get_typed_class(virt, "ElementCapabilities")
    try:
        ec_ele = assoc.AssociatorNames(ip,
                                       assoc_cn, 
                                       cn,
                                       InstanceID = id)
    except Exception:
        logger.error(CIM_ERROR_ASSOCIATORNAMES, assoc_cn)
        status = FAIL

    return status, ec_ele 

def filter(list, cn, exp_result):
    new_list = assoc.filter_by_result_class(list, cn)
    if len(new_list) != exp_result:
        logger.error("Expected %d host, got %d" % (exp_result, len(new_list)))
        return FAIL, new_list
    return PASS, new_list

def verify_host(inst_list, host_name, host_ccn):
    status, list = filter(inst_list, host_ccn, 1) 
    if status != PASS:
        return status

    inst = list[0]
    creationclassname = inst.keybindings['CreationClassName']
    name = inst.keybindings['Name']

    if creationclassname != host_ccn:
        logger.error("CreationClassName doesn't match")
        return FAIL

    if name != host_name:
        logger.error("Name doesn't match")
        return FAIL

    return PASS

def verify_service(inst_list, ip, virt, host_name, host_ccn,
                   name, ser_cn):
    status, list = filter(inst_list, ser_cn, 1) 
    if status != PASS:
        return status

    inst = list[0]
    keys = { 
              'CreationClassName'       : ser_cn, 
              'Name'                    : name,
              'SystemName'              : host_name,
              'SystemCreationClassName' : host_ccn
           }   
    try:
        service = GetInstance(ip, ser_cn, keys)
    except Exception, detail:
        logger.error(CIM_ERROR_GETINSTANCE, ser_cn)
        logger.error("Exeption : %s", detail)
        return FAIL

    creationclassname = inst.keybindings['CreationClassName']
    name = inst.keybindings['Name']

    if creationclassname != service.CreationClassName:
        logger.error("CreationClassName doesn't match")
        return FAIL

    if name != service.Name:
        logger.error("InstanceID doesn't match")
        return FAIL
    return PASS

@do_main(sup_types)
def main():
    options = main.options

    cap_list = {"VirtualSystemManagementCapabilities" : "ManagementCapabilities",
                "VirtualSystemMigrationCapabilities"  : "MigrationCapabilities"}

    status, host_name, host_ccn = get_host_info(options.ip, options.virt)
    if status != PASS:
        logger.error("Failed to get host info")
        return status

    for k, v in cap_list.iteritems():
        cn = get_typed_class(options.virt, k)
        status, ec_ele = call_assoc(options.ip, cn, v, options.virt)
        if status != PASS:
            return FAIL

        status = verify_host(ec_ele, host_name, host_ccn)
        if status != PASS:
            return status 

        if v == 'ManagementCapabilities':
            cn = get_typed_class(options.virt, "VirtualSystemManagementService")
            status = verify_service(ec_ele, options.ip, options.virt, 
                                    host_name, host_ccn,
                                    "Management Service", cn)
        else:
            cn = get_typed_class(options.virt, "VirtualSystemMigrationService")
            status = verify_service(ec_ele, options.ip, options.virt, 
                                    host_name, host_ccn,
                                    "MigrationService", cn)
        if status != PASS:
            return status 

    virtxml = vxml.get_class(options.virt)
    cxml = virtxml(test_dom)
    ret = cxml.cim_define(options.ip)
    if not ret:
        logger.error("Failed to define the dom: %s" % test_dom)
        return FAIL

    cs = live.domain_list(options.ip, options.virt)
    for system in cs:
        cn = get_typed_class(options.virt, "EnabledLogicalElementCapabilities")
        status, elec_cs = call_assoc(options.ip, cn, system, options.virt)
        if status != PASS:
            cxml.undefine(options.ip)
            return FAIL

        if len(elec_cs) < 1:
            logger.error("No ELEC instances returned")
            cxml.undefine(options.ip)
            return FAIL

        if elec_cs[0].keybindings['CreationClassName'] != \
           get_typed_class(options.virt, "ComputerSystem"):
            logger.error("Excpeted CreationClassName %s, got %s",  
                         "ComputerSystem", 
                          elec_cs[0].keybindings['CreationClassName'])
            cxml.undefine(options.ip)
            return FAIL

        if elec_cs[0].keybindings['Name'] != system:
            logger.error("ElementCapabilities association Name error")
            cxml.undefine(options.ip)
            return FAIL

    cxml.undefine(options.ip)
    return PASS

if __name__ == "__main__":
    sys.exit(main())
