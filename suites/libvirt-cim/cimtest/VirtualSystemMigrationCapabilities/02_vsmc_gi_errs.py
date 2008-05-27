#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri<dkalaker@in.ibm.com> 
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
# returned by Xen_VSMC on giving invalid inputs.
# 1) Test by giving invalid Invalid InstanceID Key Name
# Input:
# ------
# wbemcli gi http://localhost:5988/root/virt:\
# Xen_VirtualSystemMigrationCapabilities.Wrong="RPCC" -nl
# 
# 2) Test by passing Invalid InstanceID Key Value
# Input:
# ------
# wbemcli gi http://localhost:5988/root/virt:\
# Xen_VirtualSystemMigrationCapabilities.InstanceID="Wrong" -nl
# 
# Inboth the cases the following exception is verified.
# 
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND 
# error desc  : "No such instance (InstanceID)"
#
#                                                   -Date 20.02.2008

import sys
import pywbem
from XenKvmLib import assoc
from CimTest.Globals import logger, CIM_USER, CIM_PASS, CIM_NS
from CimTest.Globals import do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.common_util import try_getinstance
from XenKvmLib.classes import get_typed_class

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']

expr_values = {
                "invalid_instid" :  { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                      'desc' : 'No such instance (InstanceID)' }
              }

@do_main(sup_types)
def main():
    options = main.options

    status = PASS
    conn = assoc.myWBEMConnection('http://%s' % options.ip, (CIM_USER, CIM_PASS), CIM_NS)
    classname = get_typed_class(options.virt, 'VirtualSystemMigrationCapabilities')

    field = 'INVALID_Instid_KeyName'
    keys = { field : "RPCC" }
    ret_value = try_getinstance(conn, classname, keys, field_name=field, \
                                 expr_values=expr_values['invalid_instid'], bug_no="")
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid InstanceID Key Name.------")
        status = ret_value

    field = 'INVALID_Instid_KeyValue'
    keys = { 'InstanceID' : field }
    ret_value = try_getinstance(conn, classname, keys, field_name=field, \
                                 expr_values=expr_values['invalid_instid'], bug_no="")
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid InstanceID Key Value.------")
        status = ret_value

    return status
if __name__ == "__main__":
    sys.exit(main())
