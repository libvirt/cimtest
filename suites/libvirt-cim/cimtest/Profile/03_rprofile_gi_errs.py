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
# 1) Test by passing Invalid InstanceID Key Value
# Input:
# ------
# wbemcli gi http://localhost:5988/root/interop:\
# Xen_RegisteredProfile.InstanceID="Wrong" -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "Profile instance not found"
#
# 2) Test by giving Invalid InstanceID Key Name
# Input:
# ------
# wbemcli gi http://localhost:5988/root/interop:\
# Xen_RegisteredProfile.Wrong=<InstanceID> -nl
#
# Output:
# -------
# error code  : CIM_ERR_FAILED
# error desc  : "No InstanceID specified"
#                                                   -Date 25.02.2008

import sys
import pywbem
from VirtLib import utils
from XenKvmLib import assoc
from XenKvmLib.common_util import try_getinstance
from CimTest.ReturnCodes import PASS, FAIL
from CimTest import Globals
from CimTest.Globals import do_main

sup_types = ['Xen', 'LXC']

expr_values = {
                "invalid_instid_keyvalue" :  { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                               'desc' : "No such instance" },
                "invalid_instid_keyname" :  {  'rc'   : pywbem.CIM_ERR_FAILED, \
                                               'desc' : "No InstanceID specified" } \
              }


@do_main(sup_types)
def main():
    options = main.options

    prev_namespace = Globals.CIM_NS
    Globals.CIM_NS = 'root/interop'
    classname = 'Xen_RegisteredProfile'
    status = PASS

    conn = assoc.myWBEMConnection('http://%s' % options.ip, ( \
                                Globals.CIM_USER, Globals.CIM_PASS), Globals.CIM_NS)

    inst_id = ["CIM:DSP1042-SystemVirtualization-1.0.0", "CIM:DSP1057-VirtualSystem-1.0.0a"]

    # 1) Test by passing Invalid InstanceID Key Value
    field = 'INVALID_Instid_KeyValue'
    keys = { 'InstanceID' : field }
    ret_value = try_getinstance(conn, classname, keys, field_name=field, \
                                 expr_values=expr_values['invalid_instid_keyvalue'], bug_no="")
    if ret_value != PASS:
        Globals.logger.error("------ FAILED: Invalid InstanceID Key Value.------")
        status = ret_value

    # 2) Test by giving Invalid InstanceID Key Name
    for i in range(len(inst_id)):
        field = 'INVALID_Instid_KeyName'
        keys = { field : inst_id[i] }
        ret_value = try_getinstance(conn, classname, keys, field_name=field, \
                                 expr_values=expr_values['invalid_instid_keyname'], bug_no="")
        if ret_value != PASS:
            Globals.logger.error("------ FAILED: Invalid InstanceID Key Name.------")
            status = ret_value

    Globals.CIM_NS = prev_namespace
    return status

if __name__ == "__main__":
    sys.exit(main())
