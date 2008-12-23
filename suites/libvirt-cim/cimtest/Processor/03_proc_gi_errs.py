#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Anoop V Chakkalakkal<anoop.vijayan@in.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
#    Deepti B. kalakeri <deeptik@linux.vnet.ibm.com>
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
# returned by Xen_Processor on giving invalid inputs.
#
# Test by passing Invalid Keyvalue for following keys:
# Input:
# ------
#  CreationClassName
#  DeviceID
#  SystemCreationClassName
#  SystemName

# Format:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:Xen_Processor.\
# CreationClassName="wrong",DeviceID="Domain-0/0",SystemCreationClassName=\
# "Xen_ComputerSystem",SystemName="Domain-0"' -nl
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
from XenKvmLib.classes import get_typed_class
from XenKvmLib.vxml import get_class
from XenKvmLib.test_doms import destroy_and_undefine_all
from XenKvmLib.const import do_main, get_provider_version
from XenKvmLib.enumclass import GetInstance, CIM_CimtestClass, EnumInstances

sup_types = ['Xen', 'KVM', 'XenFV']

expected_values = {
   "invalid_sysname" : {'rc'   : CIM_ERR_NOT_FOUND,
                        'desc' : "No such instance (SystemName)" },
   "invalid_ccname" : {'rc'   : CIM_ERR_NOT_FOUND,
                       'desc' : "No such instance (CreationClassName)" },
   "invalid_sccname" : {'rc'   : CIM_ERR_NOT_FOUND,
                        'desc' : "No such instance (SystemCreationClassName)" },
   "invalid_devid"  : {'rc'   : CIM_ERR_NOT_FOUND,
                       'desc' : "No such instance " }
              }

test_dom = "proc_domain"
test_vcpus = 1

err_msg_changeset = 682

def get_proc_inst(virt, ip, cn, guest_name):
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

    vsxml = get_class(options.virt)(test_dom, vcpus=test_vcpus)
    ret = vsxml.cim_define(options.ip)
    if not ret:
        logger.error("Failed to define the guest: %s", test_dom)
        return FAIL

    status = vsxml.cim_start(options.ip)
    if status != PASS:
        logger.error("Failed to start the guest: %s", test_dom)
        vsxml.undefine(options.ip)
        return FAIL

    rev, changeset = get_provider_version(options.virt, options.ip)
    if rev < err_msg_changeset:
        old_ret = { 'rc' : CIM_ERR_NOT_FOUND,
                    'desc' : "No such instance (invalid_devid)"
                  }
        expected_values["invalid_devid"] = old_ret

    ccn  = get_typed_class(options.virt, "Processor")

    proc, status = get_proc_inst(options.virt, options.ip, ccn, test_dom)
    if status != PASS:
        vsxml.undefine(options.ip)
        return status

    key_vals = { 'SystemName'              : proc.SystemName,
                 'CreationClassName'       : proc.CreationClassName,
                 'SystemCreationClassName' : proc.SystemCreationClassName,
                 'DeviceID'                : proc.DeviceID
               }

    tc_scen = {
                'invalid_sysname'   : 'SystemName',
                'invalid_ccname'    : 'CreationClassName',
                'invalid_sccname'   : 'SystemCreationClassName',
                'invalid_devid'     : 'DeviceID',
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

    vsxml.cim_destroy(options.ip)
    vsxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())
