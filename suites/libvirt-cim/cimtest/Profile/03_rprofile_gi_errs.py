#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Anoop V Chakkalakkal<anoop.vijayan@in.ibm.com>
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
# returned by Xen_RegisteredProfile on giving invalid inputs.
#
# 1) Test by giving Invalid InstanceID Key Name
# Input:
# ------
# wbemcli gi http://localhost:5988/root/interop:\
# Xen_RegisteredProfile.Wrong=<InstanceID> -nl
#
# Output:
# -------
# error code  : CIM_ERR_FAILED
# error desc  : "No InstanceID specified"

import sys
from pywbem import CIM_ERR_NOT_FOUND, CIMError
from pywbem.cim_obj import CIMInstanceName
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import logger
from CimTest import Globals
from XenKvmLib.const import do_main
from XenKvmLib.classes import get_typed_class
from XenKvmLib.enumclass import GetInstance, CIM_CimtestClass

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

@do_main(sup_types)
def main():
    options = main.options

    prev_namespace = Globals.CIM_NS
    Globals.CIM_NS = 'root/interop'

    cn = get_typed_class(options.virt, 'RegisteredProfile')

    expr_values = {
                   'rc'   : CIM_ERR_NOT_FOUND,
                   'desc' : "No such instance"
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
        logger.error("Unexpected errno %s, desc %s", err_no, err_desc)
        logger.error("Expected %s %s", exp_desc, exp_rc)

    if status != PASS:
        logger.error("------ FAILED: InstanceID Key Value. ------")

    Globals.CIM_NS = prev_namespace
    return status

if __name__ == "__main__":
    sys.exit(main())
