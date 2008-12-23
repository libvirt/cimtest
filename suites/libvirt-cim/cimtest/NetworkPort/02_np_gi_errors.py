#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Author:
#   Anoop V Chakkalakkal
#   Guolian Yun <yunguol@cn.ibm.com>
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
# returned by Xen_NetworkPort on giving invalid inputs.
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
# wbemcli gi 'http://localhost:5988/root/virt:KVM_NetworkPort.DeviceID="wrong",
# SystemCreationClassName="KVM_ComputerSystem", SystemName="guest",
# CreationClassName="KVM_NetworkPort"'
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (DeviceID)" (this varies by key)
#

import sys
from pywbem import CIM_ERR_NOT_FOUND, CIMError
from pywbem.cim_obj import CIMInstanceName
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from CimTest.Globals import logger
from XenKvmLib.classes import get_typed_class
from XenKvmLib.vxml import get_class
from XenKvmLib.const import do_main, LXC_netns_support
from XenKvmLib.enumclass import GetInstance, CIM_CimtestClass, EnumInstances

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

def get_net_inst(virt, ip, cn, guest_name):
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

    test_dom = "nettest_domain"
    test_mac = "00:11:22:33:44:55"

    if options.virt =='LXC' and LXC_netns_support is False:
        return SKIP  

    vsxml = get_class(options.virt)(test_dom, mac=test_mac)
    ret = vsxml.cim_define(options.ip)
    if ret != 1:
        logger.error("Define domain failed!")
        return FAIL 

    expr_values = {
                   'rc'   : CIM_ERR_NOT_FOUND,
                   'desc' : 'No such instance'
                  }

    cn = get_typed_class(options.virt, 'NetworkPort')

    net, status = get_net_inst(options.virt, options.ip, cn, test_dom)
    if status != PASS:
        vsxml.undefine(options.ip)
        return status

    key_vals = { 'SystemName'              : net.SystemName,
                 'CreationClassName'       : net.CreationClassName,
                 'SystemCreationClassName' : net.SystemCreationClassName,
                 'DeviceID'                : net.DeviceID
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
