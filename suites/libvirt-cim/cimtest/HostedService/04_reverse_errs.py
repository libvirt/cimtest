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
import pywbem
from pywbem.cim_obj import CIMInstanceName
from XenKvmLib import assoc
from XenKvmLib import enumclass
from XenKvmLib.common_util import get_host_info, try_assoc
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE, CIM_USER, \
                            CIM_PASS, CIM_NS
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL, XFAIL

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']
exp_values = {
              "invalid_ccname" : {"rc" : pywbem.CIM_ERR_NOT_FOUND, 
                        "desc" : "No such instance (CreationClassName)"},       
              "invalid_name"   : {"rc" : pywbem.CIM_ERR_NOT_FOUND, 
                        "desc" : "No such instance (Name)"}
             }

@do_main(sup_types)
def main():
    options = main.options
    status = FAIL
    keys = ['Name', 'CreationClassName']
    status, host_inst = get_host_info(options.ip, options.virt)
    if status != PASS:
        logger.error("Error in calling get_host_info function")
        return FAIL

    host_ccn = host_inst.CreationClassName
    host_name = host_inst.Name

    rpcs = get_typed_class(options.virt, "ResourcePoolConfigurationService")
    vsms = get_typed_class(options.virt, "VirtualSystemManagementService")
    migrate = get_typed_class(options.virt, "VirtualSystemMigrationService")
    
    servicelist = {rpcs : "RPCS",
                   vsms : "Management Service",
                   migrate : "MigrationService"}
                                              
    
    conn = assoc.myWBEMConnection('http://%s' % options.ip,
                                  (CIM_USER, CIM_PASS),
                                   CIM_NS)
    assoc_classname = get_typed_class(options.virt, "HostedService")
    for k, v in servicelist.items():

        keys = {"Wrong" : v, "CreationClassName": k,
                "SystemCreationClassName": host_ccn,  "SystemName" : host_name}
        ret =  try_assoc(conn, k, assoc_classname, keys, "Name",
                         exp_values['invalid_name'], bug_no="")
        if ret != PASS:
            logger.error("------ FAILED: Invalid Name Key Name.------")
            return FAIL

        keys = {"Name" : v, "Wrong": k,  "SystemCreationClassName":  host_ccn,
                "SystemName" : host_name}
        ret =  try_assoc(conn, k, assoc_classname, keys, "Name",
                         exp_values['invalid_ccname'], bug_no="")
        if ret != PASS:
            logger.error("------ FAILED: Invalid Name Key Name.------")
            return FAIL
                
    return PASS 


if __name__ == "__main__":
    sys.exit(main())
