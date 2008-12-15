#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Author:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
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
# This tc is used to verify if appropriate exceptions are 
# returned by ResourcePoolConfigurationService on giving invalid inputs.
# 
# Input values for the following keys:
# ------------------------------------
#   CreationClassName
#   Name
#   SystemCreationClassName
#   SystemName 
# 
# Format
# ------
# wbemcli gi 'http://localhost:5988/root/virt:\
# Xen_ResourcePoolConfigurationService.CreationClassName="Wrong",\
# Name="RPCS",SystemCreationClassName="Xen_HostSystem",\
# SystemName="mx3650a.in.ibm.com"'
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND 
# error desc  : "No such instance (CreationClassName)" (varies by key name)
#

import sys
from pywbem import CIM_ERR_NOT_FOUND, CIMError
from pywbem.cim_obj import CIMInstanceName
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from XenKvmLib.classes import get_typed_class
from XenKvmLib.enumclass import GetInstance, CIM_CimtestClass, EnumInstances

platform_sup = ['Xen', 'KVM', 'XenFV', 'LXC']

expected_values = {
 "invalid_ccname"  :  { 'rc'   : CIM_ERR_NOT_FOUND,
                        'desc' : 'No such instance (CreationClassName)' },
 "invalid_sccname" :  { 'rc'   : CIM_ERR_NOT_FOUND,
                        'desc' : 'No such instance (SystemCreationClassName)' },
 "invalid_name"    :  { 'rc'   : CIM_ERR_NOT_FOUND,
                        'desc' : 'No such instance (Name)'},
 "invalid_sysval"  :  { 'rc'   : CIM_ERR_NOT_FOUND,
                        'desc' : 'No such instance (SystemName)' },
              }

def get_rpcs_inst(virt, ip, cn):
    try:
        enum_list = EnumInstances(ip, cn)

        if len(enum_list) != 1:
            logger.error("No %s instances returned", cn)
            return None, FAIL

        return enum_list[0], PASS

    except Exception, details:
        logger.error(details)

    return None, FAIL

@do_main(platform_sup)
def main():
    options = main.options
    server = options.ip
    virt = options.virt

    cn = get_typed_class(virt, 'ResourcePoolConfigurationService')

    rpcs, status = get_rpcs_inst(options.virt, options.ip, cn)
    if status != PASS:
        return status

    key_vals = { 'SystemName'              : rpcs.SystemName,
                 'CreationClassName'       : rpcs.CreationClassName,
                 'SystemCreationClassName' : rpcs.SystemCreationClassName,
                 'Name'                    : rpcs.Name 
               }

    tc_scen = {
                'invalid_ccname'   : 'CreationClassName',
                'invalid_sccname'  : 'SystemCreationClassName',
                'invalid_name'     : 'Name',
                'invalid_sysval'   : 'SystemName',
              }

    for tc, field in tc_scen.iteritems():
        status = FAIL

        keys = key_vals.copy()
        keys[field] = tc 
        expr_values = expected_values[tc]

        ref = CIMInstanceName(cn, keybindings=keys)

        try:
            inst = CIM_CimtestClass(server, ref)

        except CIMError, (err_no, err_desc):
            exp_rc    = expr_values['rc']
            exp_desc  = expr_values['desc']

            if err_no == exp_rc and err_desc.find(exp_desc) >= 0:
                logger.info("Got expected exception: %s %s", exp_desc, exp_rc)
                status = PASS
            else:
                logger.error("Unexpected errno %s, desc %s", err_no, err_desc)
                logger.error("Expected %s %s", exp_desc, exp_rc)

        if status != PASS:
            logger.error("------ FAILED: %s ------", tc)
            break

    return status
if __name__ == "__main__":
    sys.exit(main())
