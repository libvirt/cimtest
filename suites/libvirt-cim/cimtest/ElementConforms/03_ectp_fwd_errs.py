#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Anoop V Chakkalakkal<anoop.vijayan@in.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
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
# Testcase description
#
# 1. Verify Xen_ElementConformsToProfile association returns error when invalid
# InstanceID keyname is supplied
#
# Input
# -----
# wbemcli ain -ac Xen_ElementConformsToProfile 'http://localhost:\
# 5988/root/interop:Xen_RegisteredProfile.wrong= \
# "CIM:DSP1042-SystemVirtualization-1.0.0"' -nl
#
# Output
# ------
# rc   : CIM_ERR_FAILED
# desc : "No InstanceID specified"
#
# 2. Verify Xen_ElementConformsToProfile association returns error when invalid
# InstanceID keyvalue is supplied
#
# Input
# -----
# wbemcli ain -ac Xen_ElementConformsToProfile 'http://localhost:\
# 5988/root/interop:Xen_RegisteredProfile.InstanceID="wrong"' -nl
#
# Output
# ------
# REVISIT: Currently  the provider is not returning errors
# Set appropriate values in exp_desc and exp_rc once fixed.
#
#                                                Date : 03-03-2008

import sys
import pywbem
from VirtLib import utils
from XenKvmLib import assoc
from XenKvmLib.common_util import try_assoc
from XenKvmLib.classes import get_typed_class
from CimTest.ReturnCodes import PASS, FAIL
from CimTest import Globals
from CimTest.Globals import logger, CIM_USER, CIM_PASS
from XenKvmLib.const import do_main

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']


expr_values = {
        "INVALID_InstID_Keyname"  : { 'rc'   : pywbem.CIM_ERR_FAILED, \
                                      'desc' : 'No InstanceID specified' }, \
        "INVALID_InstID_Keyvalue" : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                      'desc' : 'No such instance' }
      }

def try_invalid_assoc(name_val, i, field, virt="Xen"):
    classname = get_typed_class(virt, "RegisteredProfile")
    ac_classname = get_typed_class(virt, "ElementConformsToProfile")
    j = 0
    keys = {}
    temp = name_val[i]
    name_val[i] = field
    for j in range(len(name_val)/2):
        k = j * 2
        keys[name_val[k]] = name_val[k+1]
    ret_val = try_assoc(conn, classname, ac_classname, keys, field_name=field, \
                              expr_values=expr_values[field], bug_no="")
    if ret_val != PASS:
        logger.error("------ FAILED: %s------", field)
    name_val[i] = temp
    return ret_val


@do_main(sup_types)
def main():
    options = main.options

    status = PASS
    prev_namespace = Globals.CIM_NS
    Globals.CIM_NS = 'root/interop'

    global conn
    conn = assoc.myWBEMConnection('http://%s' % options.ip, (CIM_USER, \
    CIM_PASS), Globals.CIM_NS)

    sv_name_val = ['InstanceID', 'CIM:DSP1042-SystemVirtualization-1.0.0']
    vs_name_val = ['InstanceID', 'CIM:DSP1057-VirtualSystem-1.0.0a']
    tc_scen     = ['INVALID_InstID_Keyname', 'INVALID_InstID_Keyvalue']

    for i in range(len(tc_scen)):
        retval = try_invalid_assoc(sv_name_val, i, tc_scen[i], options.virt)
        if retval != PASS:
            status = retval

    for i in range(len(tc_scen)):
        retval = try_invalid_assoc(vs_name_val, i, tc_scen[i], options.virt)
        if retval != PASS:
            status = retval

    Globals.CIM_NS = prev_namespace
    return status
if __name__ == "__main__":
    sys.exit(main())


