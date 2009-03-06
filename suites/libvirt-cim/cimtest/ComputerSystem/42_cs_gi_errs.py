#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Anoop V Chakkalakkal<anoop.vijayan@in.ibm.com>
#    Zhengang Li <lizg@cn.ibm.com>
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
# returned by ComputerSystem on giving invalid inputs.
#
# 1) Test by passing Invalid Key Values for the following
# Input:
# ------
#    CreationClassName
#    Name
#
# Format:
# --------
# wbemcli gi http://localhost:5988/root/virt:Xen_ComputerSystem.\
# CreationClassName="Xen_ComputerSystem",Name="INVALID_Name_KeyValue" -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (INVALID_Name_KeyValue)" (varies by key)
#

import sys
from pywbem import CIM_ERR_NOT_FOUND, CIMError
from pywbem.cim_obj import CIMInstanceName
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import logger
from XenKvmLib import vxml
from XenKvmLib.classes import get_typed_class
from XenKvmLib.const import do_main, get_provider_version
from XenKvmLib.enumclass import GetInstance, CIM_CimtestClass, EnumInstances

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
libvirt_err_changes = 821

expected_values = {
           "invalid_name"   : {'rc'   : CIM_ERR_NOT_FOUND,
                               'desc' : "No such instance (invalid_name)" },
           "invalid_ccname" : {'rc'   : CIM_ERR_NOT_FOUND,
                               'desc' : "No such instance (CreationClassName)" }
                  }


def get_cs_inst(virt, ip, cn, guest_name):
    try:
        enum_list = EnumInstances(ip, cn)

        if enum_list < 1:
            logger.error("No %s instances returned", cn)
            return None, FAIL

        for guest in enum_list:
            if guest.Name == guest_name:
                return guest, PASS

    except Exception, details:
        logger.error(details)

    return None, FAIL

@do_main(sup_types)
def main():
    options = main.options

    inst_name = 'ETdomain'
    cxml = vxml.get_class(options.virt)(inst_name)
    ret = cxml.cim_define(options.ip)
    if not ret:
        logger.error("Unable to define guest %s", inst_name)
        return FAIL

    cn = get_typed_class(options.virt, 'ComputerSystem')

    cs, status = get_cs_inst(options.virt, options.ip, cn, inst_name)
    if status != PASS:
        return status

    key_vals = { 'Name'               : cs.Name,
                 'CreationClassName'  : cs.CreationClassName,
               }

    tc_scen = {
                'invalid_name'     : 'Name',
                'invalid_ccname'   : 'CreationClassName',
              }

    for tc, field in tc_scen.iteritems():
        status = FAIL

        keys = key_vals.copy()
        keys[field] = tc
        expr_values = expected_values[tc]

        ref = CIMInstanceName(cn, keybindings=keys)

        curr_cim_rev, changeset = get_provider_version(options.virt, options.ip)
        if tc == 'invalid_name' and curr_cim_rev >= libvirt_err_changes:
            expr_values['desc'] = "Referenced domain `invalid_name'" + \
                                  " does not exist: Domain not found"

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

    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())
