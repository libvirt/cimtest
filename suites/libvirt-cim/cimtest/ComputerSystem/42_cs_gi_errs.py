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
# returned by Xen_ComputerSystem on giving invalid inputs.
#
# 1) Test by passing Invalid Name Key Value
# Input:
# ------
# wbemcli gi http://localhost:5988/root/virt:Xen_ComputerSystem.\
# CreationClassName="Xen_ComputerSystem",Name="INVALID_Name_KeyValue" -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (INVALID_Name_KeyValue)"
#
# 2) Test by giving Invalid Name Key Name
# Input:
# ------
# wbemcli gi http://localhost:5988/root/virt:Xen_ComputerSystem.\
# CreationClassName="Xen_ComputerSystem",INVALID_Name_KeyName="Domain-0" -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No domain name specified"
#
# 3) Test by passing Invalid CCName Key Value
# Input:
# ------
# wbemcli gi http://localhost:5988/root/virt:Xen_ComputerSystem.\
# CreationClassName="Xen_INVALID_CCName_KeyValue",Name="Domain-0" -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (CreationClassName)"
#
# 4) Test by giving Invalid CCName Key Name
# Input:
# ------
# wbemcli gi http://localhost:5988/root/virt:Xen_ComputerSystem.\
# INVALID_CCName_KeyName="Xen_ComputerSystem",Name="Domain-0" -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (CreationClassName)"
#                                                   -Date 22.02.2008

import sys
import pywbem
from VirtLib import utils
from XenKvmLib import assoc
from XenKvmLib import vxml
from XenKvmLib.classes import get_typed_class
from XenKvmLib.common_util import try_getinstance
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import logger, CIM_USER, CIM_PASS, CIM_NS
from XenKvmLib.const import do_main, VIRSH_ERROR_DEFINE


sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

expr_values = {
    "invalid_name_keyvalue"   : {'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                 'desc' : "No such instance (INVALID_Name_KeyValue)" }, \
    "invalid_name_keyname"    : {'rc'   : pywbem.CIM_ERR_FAILED, \
                                 'desc' : "No domain name specified" }, \
    "invalid_ccname"          : {'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                 'desc' : "No such instance (CreationClassName)" }
              }


@do_main(sup_types)
def main():
    options = main.options

    inst_ccname = classname = get_typed_class(options.virt, 'ComputerSystem')
    inst_name = 'ETdomain'
    cxml = vxml.get_class(options.virt)(inst_name)
    ret = cxml.cim_define(options.ip)
    if not ret:
        logger.error(VIRSH_ERROR_DEFINE % inst_name)
        return FAIL

    status = PASS
    conn = assoc.myWBEMConnection('http://%s' % options.ip, (CIM_USER, CIM_PASS), CIM_NS)

    # 1) Test by passing Invalid Name Key Value
    field = 'INVALID_Name_KeyValue'
    keys = { 'Name' : field, 'CreationClassName' : inst_ccname }
    ret_value = try_getinstance(conn, classname, keys, field_name=field, \
                                 expr_values=expr_values['invalid_name_keyvalue'], bug_no="")
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid Name Key Value.------")
        status = ret_value

    # 2) Test by giving Invalid Name Key Name
    field = 'INVALID_Name_KeyName'
    keys = { field : inst_name, 'CreationClassName' : inst_ccname }
    ret_value = try_getinstance(conn, classname, keys, field_name=field, \
                                 expr_values=expr_values['invalid_name_keyname'], bug_no="")
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid Name Key Name.------")
        status = ret_value

    # 3) Test by passing Invalid CCName Key Value
    field = 'INVALID_CCName_KeyValue'
    keys = { 'Name' : inst_name, 'CreationClassName' : field }
    ret_value = try_getinstance(conn, classname, keys, field_name=field, \
                                 expr_values=expr_values['invalid_ccname'], bug_no="")
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid CCName Key Value.------")
        status = ret_value

    # 4) Test by giving Invalid CCName Key Name
    field = 'INVALID_CCName_KeyName'
    keys = { 'Name' : inst_name, field : inst_ccname }
    ret_value = try_getinstance(conn, classname, keys, field_name=field, \
                                 expr_values=expr_values['invalid_ccname'], bug_no="")
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid CCName Key Name.------")
        status = ret_value

    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())
