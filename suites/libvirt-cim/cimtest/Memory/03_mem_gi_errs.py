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
#
# Input:
# ------
#  DeviceID
#  SystemCreationClassName
#  SystemName
#  CreationClassName
#
# Format:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:KVM_Memory.DeviceID="wrong",
# SystemCreationClassName="KVM_ComputerSystem", SystemName="guest",
# CreationClassName="KVM_Memory"'
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (DeviceID)" (this varies by key)
#

import sys
from pywbem import CIM_ERR_NOT_FOUND, CIMError
from pywbem.cim_obj import CIMInstanceName
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import logger, CIM_USER, CIM_PASS, CIM_NS 
from XenKvmLib.vxml import get_class
from XenKvmLib.classes import get_typed_class
from XenKvmLib.const import do_main
from XenKvmLib.enumclass import GetInstance, CIM_CimtestClass, EnumInstances

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

def get_mem_inst(virt, ip, cn, guest_name):
    try:
        enum_list = EnumInstances(ip, cn)

        if enum_list < 1:
            logger.error("No %s instances returned", cn)
            return None, FAIL

        for inst in enum_list:
            if inst.SystemName == guest_name:
                return inst, PASS

    except Exception, details:
        logger.error(details)

    return None, FAIL

@do_main(sup_types)
def main():
    options = main.options

    test_dom = "domU"
    test_mem = 256 #MB

    vsxml = get_class(options.virt)(test_dom, test_mem)
    ret = vsxml.cim_define(options.ip)
    if not ret:
        logger.error("Failed to Create the dom: %s", test_dom)
        return FAIL

    expr_values = {
                   'rc'   : CIM_ERR_NOT_FOUND,
                   'desc' : 'No such instance'
                  }

    cn = get_typed_class(options.virt, "Memory")

    mem, status = get_mem_inst(options.virt, options.ip, cn, test_dom)
    if status != PASS:
        vsxml.undefine(options.ip)
        return status

    key_vals = { 'SystemName'              : mem.SystemName,
                 'CreationClassName'       : mem.CreationClassName,
                 'SystemCreationClassName' : mem.SystemCreationClassName,
                 'DeviceID'                : mem.DeviceID
               }

    tc_scen = {
                'invalid_sysval'   : 'SystemName',
                'invalid_ccname'   : 'CreationClassName',
                'invalid_sccname'  : 'SystemCreationClassName',
                'invalid_devid'    : 'DeviceID',
              }

    for tc, field in tc_scen.iteritems():
        status = FAIL

        keys = key_vals.copy()
        keys[field] = tc 

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

        if status != PASS:
            logger.error("------ FAILED: %s ------", tc)
            break

    vsxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())
