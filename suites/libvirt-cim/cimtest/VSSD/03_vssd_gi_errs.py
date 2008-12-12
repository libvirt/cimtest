#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Anoop V Chakkalakkal<anoop.vijayan@in.ibm.com>
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
# returned by Xen_VirtualSystemSettingData on giving invalid inputs.
#
# 1) Test by passing Invalid InstID Keyname
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:\
# Xen_VirtualSystemSettingData.INVALID_InstID_Keyname="Xen:new"' -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (InstanceID)"

import sys
from pywbem import CIM_ERR_NOT_FOUND, CIMError
from pywbem.cim_obj import CIMInstanceName
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from XenKvmLib.vxml import get_class
from XenKvmLib.classes import get_typed_class
from XenKvmLib.enumclass import GetInstance, CIM_CimtestClass

platform_sup = ['Xen', 'KVM', 'XenFV', 'LXC']
test_dom  = "VSSD_domain"

@do_main(platform_sup)
def main():
    options = main.options

    vsxml = get_class(options.virt)(test_dom)
    ret = vsxml.cim_define(options.ip)
    if not ret :
        logger.error("error while define of VS")
        return FAIL

    cn = get_typed_class(options.virt, 'VirtualSystemManagementCapabilities')

    expr_values = {
                    'rc'   : CIM_ERR_NOT_FOUND,
                    'desc' : "No such instance (InstanceID)"
                  }

    keys = { 'InstanceID' : 'INVALID_Instid_KeyValue' }

    ref = CIMInstanceName(cn, keybindings=keys)

    status = FAIL 
    try:
        inst = CIM_CimtestClass(options.ip, ref)

    except CIMError, (err_no, err_desc):
        exp_rc    = expr_values['rc']
        exp_desc  = expr_values['desc']

        if err_no == exp_rc and err_desc.find(exp_desc) >= 0:
            logger.info("Got expected exception: %s %s", exp_desc, exp_rc)
            status = PASS
        else:
            logger.error("Unexpected errno %s and desc %s", err_no, err_desc)
            logger.error("Expected %s %s", exp_desc, exp_rc)
            status = FAIL

    if status != PASS:
        logger.error("------ FAILED: Invalid InstanceID Key Value.------")

    vsxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())

