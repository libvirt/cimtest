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
# returned by Xen_HostSystem on giving invalid inputs.
#
# 1) Test by passing Invalid CCName Keyname
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:Xen_HostSystem.\
# Wrong="Xen_HostSystem",Name="mx3650a.in.ibm.com"' -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (CreationClassName)"
#
# 2) Test by giving Invalid CCName Keyvalue
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:Xen_HostSystem.\
# CreationClassName="Wrong",Name="mx3650a.in.ibm.com"' -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (CreationClassName)"
#
# 3) Test by passing Invalid Name Keyname
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:Xen_HostSystem.\
# CreationClassName="Xen_HostSystem",Wrong="mx3650a.in.ibm.com"' -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (Name)"
#
# 4) Test by giving Invalid CCName Keyvalue
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:Xen_HostSystem.\
# CreationClassName="Xen_HostSystem",Name="Wrong"' -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (Name)"
#
#                                                   -Date 26.02.2008

import sys
import pywbem
from VirtLib import utils
from XenKvmLib import assoc
from XenKvmLib.common_util import get_host_info, try_getinstance
from XenKvmLib.classes import get_typed_class
from optparse import OptionParser
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import logger, CIM_USER, CIM_PASS, CIM_NS
from XenKvmLib.const import do_main

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

expr_values = {
    "invalid_ccname" : {'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                 'desc' : "No such instance (CreationClassName)" }, \
    "invalid_name"   : {'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                 'desc' : "No such instance (Name)" }
              }


@do_main(sup_types)
def main():
    options = main.options
    status = PASS

    if options.virt == "XenFV":
        options.virt = 'Xen'

    status, host_name, classname = get_host_info(options.ip, options.virt)
    if status != PASS:
        return status

    conn = assoc.myWBEMConnection('http://%s' % options.ip, (CIM_USER, CIM_PASS), CIM_NS)

    # 1) Test by giving Invalid CCName Key Name
    field = 'INVALID_CCName_KeyName'
    keys = { field : classname, 'Name' : host_name }
    ret_value = try_getinstance(conn, classname, keys, field_name=field, \
                                 expr_values=expr_values['invalid_ccname'], bug_no="")
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid CCName Key Name.------")
        status = ret_value

    # 2) Test by passing Invalid CCName Key Value
    field = 'INVALID_CCName_KeyValue'
    keys = { 'CreationClassName' : field, 'Name' : host_name }
    ret_value = try_getinstance(conn, classname, keys, field_name=field, \
                                 expr_values=expr_values['invalid_ccname'], bug_no="")
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid CCName Key Value.------")
        status = ret_value

    # 3) Test by giving Invalid Name Key Name
    field = 'INVALID_Name_KeyName'
    keys = { 'CreationClassName' :  classname, field : host_name}
    ret_value = try_getinstance(conn, classname, keys, field_name=field, \
                                 expr_values=expr_values['invalid_name'], bug_no="")
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid Name Key Name.------")
        status = ret_value

    # 4) Test by passing Invalid Name Key Value
    field = 'INVALID_Name_KeyValue'
    keys = { 'CreationClassName' : classname, 'Name' : field }
    ret_value = try_getinstance(conn, classname, keys, field_name=field, \
                                 expr_values=expr_values['invalid_name'], bug_no="")
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid Name Key Value.------")
        status = ret_value

    return status

if __name__ == "__main__":
    sys.exit(main())
