#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B.Kalakeri 
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
# returned by VirtualSystemSnapshotService on giving invalid inputs.
# 
# Input:
# ------
# Invalid values for the following:  
#   CreationClassName
#   Name
#   SystemCreationClassName
#   SystemName
#   
# Format:
# --------
# wbemcli gi 'http://localhost:5988/root/virt:KVM_VirtualSystemSnapshotService. \
# CreationClassName="Wrong",Name="SnapshotService",\
# SystemCreationClassName="KVM_HostSystem",SystemName="mx3650a.in.ibm.com"' -nl
# 
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND 
# error desc  :  "No such instance (CreationClassName)" (varies by key name)

import sys
import pywbem
from pywbem import CIM_ERR_NOT_FOUND, CIMError
from pywbem.cim_obj import CIMInstanceName
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.const import do_main
from XenKvmLib.classes import get_typed_class
from XenKvmLib.common_util import get_host_info
from XenKvmLib.enumclass import GetInstance, CIM_CimtestClass, EnumInstances

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
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

def get_vsss_inst(virt, ip, cn):
    try:
        enum_list = EnumInstances(ip, cn)

        if enum_list < 1:
            logger.error("No %s instances returned", cn)
            return None, FAIL

        return enum_list[0], PASS

    except Exception, details:
        logger.error(details)

    return None, FAIL

@do_main(sup_types)
def main():
    options = main.options

    ccn  = get_typed_class(options.virt, "VirtualSystemSnapshotService")

    vsss, status = get_vsss_inst(options.virt, options.ip, ccn)
    if status != PASS:
        return status

    key_vals = { 'SystemName'              : vsss.SystemName,
                 'CreationClassName'       : vsss.CreationClassName,
                 'SystemCreationClassName' : vsss.SystemCreationClassName,
                 'Name'                    : vsss.Name 
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

        ref = CIMInstanceName(ccn, keybindings=keys)

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

        if status != PASS:
            logger.error("------ FAILED: %s ------", tc)
            break

    return status 
if __name__ == "__main__":
    sys.exit(main())
