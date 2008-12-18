#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri<dkalaker@in.ibm.com> 
#    
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
# Test Case Info:
# --------------
# This tc is used to verify if appropriate exceptions are 
# returned by AllocationCapabilities on giving invalid inputs.
#
# 1) Test by passing Invalid InstanceID Key Value
# Input:
# ------
# wbemcli gi http://localhost:5988/root/virt:\
# Xen_AllocationCapabilities.InstanceID="Wrong" -nl
# 
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND 
# error desc  : "Instance not found"
#

import sys
from pywbem import CIM_ERR_NOT_FOUND, CIMError
from pywbem.cim_obj import CIMInstanceName
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, SKIP, FAIL
from XenKvmLib.const import do_main
from XenKvmLib.classes import get_typed_class
from XenKvmLib.enumclass import GetInstance, CIM_CimtestClass, EnumInstances
from XenKvmLib.common_util import parse_instance_id

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

def enum_ac(virt, ip, cn):
    ac_ids = [] 

    try:
        enum_list = EnumInstances(ip, cn)

        if enum_list < 1:
            logger.error("No %s instances returned", cn)
            return ac_ids, FAIL

        for ac in enum_list:
            pool, id, status = parse_instance_id(ac.InstanceID)
            if status != PASS:
                logger.error("Unable to parse InstanceID: %s" % ac.InstanceID)
                return ac_ids, FAIL

            ac_ids.append("%s/invalid_id" % pool)

        ac_ids.append("invalid_id")

    except Exception, details:
        logger.error(details)
        return ac_ids, FAIL

    return ac_ids, PASS

@do_main(sup_types)     
def main():

    options = main.options
    server = options.ip
    virt = options.virt

    cn = get_typed_class(virt, "AllocationCapabilities") 

    ac_id_list, status = enum_ac(virt, server, cn)
    if status != PASS:
        logger.error("Unable to enumerate %s instances", cn)
        return FAIL

    expr_values = {
                    'rc'   : CIM_ERR_NOT_FOUND,
                    'desc' : "Instance not found"
                  }

    for id in ac_id_list:
        status = FAIL
        keys = { 'InstanceID' : id }

        ref = CIMInstanceName(cn, keybindings=keys)

        try:
            inst = CIM_CimtestClass(options.ip, ref)

        except CIMError, (err_no, err_desc):
            exp_rc    = expr_values['rc']
            exp_desc  = expr_values['desc']

            if err_no == exp_rc and err_desc.find(exp_desc) >= 0:
                logger.info("Got expected exception: %s %s", exp_desc, exp_rc)
                status = PASS
            else:
                logger.error("Unexpected errno %s, desc %s", err_no, err_desc)
                logger.error("Expected %s %s", exp_desc, exp_rc)
                status = FAIL

        if status != PASS:
            logger.error("------ FAILED: Invalid InstanceID %s ------", id)
            break

    return status
if __name__ == "__main__":
    sys.exit(main())
