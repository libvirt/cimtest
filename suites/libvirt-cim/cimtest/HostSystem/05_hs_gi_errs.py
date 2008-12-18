#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Anoop V Chakkalakkal<anoop.vijayan@in.ibm.com>
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
# Test Case Info:
# --------------
# This tc is used to verify if appropriate exceptions are
# returned by HostSystem on giving invalid inputs.
#
# 1) Test by passing invalid values for the following keys: 
#
# Input:
# ------
#  CreationClassName
#  Name
#
# Format:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:Xen_HostSystem.\
# CreationClassName="Wrong",Name="x3650"' -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (CreationClassName)" (varies by key)
#

import sys
from pywbem import CIM_ERR_NOT_FOUND, CIMError
from pywbem.cim_obj import CIMInstanceName
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from CimTest.Globals import logger
from XenKvmLib.common_util import get_host_info
from XenKvmLib.classes import get_typed_class
from XenKvmLib.const import do_main
from XenKvmLib.enumclass import GetInstance, CIM_CimtestClass, EnumInstances

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

expected_values = {
                   "invalid_name"   : {'rc'   : CIM_ERR_NOT_FOUND, 
                                       'desc' : "No such instance (Name)" },
                   "invalid_ccname" : {'rc'   : CIM_ERR_NOT_FOUND, 
                                       'desc' : "No such instance "
                                                "(CreationClassName)" }
                 }

@do_main(sup_types)
def main():
    options = main.options
    status = PASS

    if options.virt == "XenFV":
        options.virt = 'Xen'

    status, host_inst = get_host_info(options.ip, options.virt)
    if status != PASS:
        return status

    #Test calls GetInstance() - no need to test GetInstance() of SBLIM providers
    if (host_inst.Classname == "Linux_ComputerSystem"):
        return SKIP

    key_vals = { 'Name'              : host_inst.Name,
                 'CreationClassName' : host_inst.CreationClassName,
               }

    tc_scen = {
                'invalid_name'   : 'Name',
                'invalid_ccname' : 'CreationClassName',
              }

    for tc, field in tc_scen.iteritems():
        status = FAIL

        keys = key_vals.copy()
        keys[field] = tc
        expr_values = expected_values[tc]

        ref = CIMInstanceName(host_inst.Classname, keybindings=keys)

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
