#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Anoop V Chakkalakkal<anoop.vijayan@in.ibm.com>
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
# Testcase description
#
# Verify Xen_ElementConformsToProfile association returns error when invalid
# CreationClassname keyname is supplied
#
# Input
# -----
# wbemcli ain -ac Xen_ElementConformsToProfile 'http://localhost:\
# 5988/root/virt:Xen_HostSystem.wrong="Xen_HostSystem",Name="mx3650a.in.ibm.com"' -nl
#
# Output
# ------
# REVISIT: Currently  the provider is returning the records instead of exception.
#          Set appropriate values in exp_desc and exp_rc once fixed.
#
#
# Verify Xen_ElementConformsToProfile association returns error when invalid
# CreationClassname keyvalue is supplied
#
# Input
# -----
# wbemcli ain -ac Xen_ElementConformsToProfile 'http://localhost:\
# 5988/root/virt:Xen_HostSystem.CreationClassName="wrong",Name="mx3650a.in.ibm.com"' -nl
#
# Output
# ------
# REVISIT: Currently  the provider is returning the records instead of exception.
#          Set appropriate values in exp_desc and exp_rc once fixed.
#
# Verify Xen_ElementConformsToProfile association returns error when invalid
# Name keyname is supplied
#
# Input
# -----
# wbemcli ain -ac Xen_ElementConformsToProfile 'http://localhost:\
# 5988/root/virt:Xen_HostSystem.CreationClassName="Xen_HostSystem",\
# wrong="mx3650a.in.ibm.com"' -nl
#
# Output
# ------
# REVISIT: Currently  the provider is returning the records instead of exception.
#          Set appropriate values in exp_desc and exp_rc once fixed.
#
#
# Verify Xen_ElementConformsToProfile association returns error when invalid
# Name keyvalue is supplied
#
# Input
# -----
# wbemcli ain -ac Xen_ElementConformsToProfile 'http://localhost:\
# 5988/root/virt:Xen_HostSystem.CreationClassName="Xen_HostSystem",Name="wrong"' -nl
#
# Output
# ------
# REVISIT: Currently  the provider is returning the records instead of exception.
#          Set appropriate values in exp_desc and exp_rc once fixed.
#
#                                                Date : 03-03-2008

import sys
import pywbem
from VirtLib import utils, live
from XenKvmLib import assoc
from XenKvmLib.common_util import try_assoc
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import log_param, logger, CIM_USER, CIM_PASS, CIM_NS, do_main

sup_types = ['Xen']

ac_classname = 'Xen_ElementConformsToProfile'
bug          = '92642'

expr_values = {
                "INVALID_CCName_Keyname"  : { 'rc' : '' , 'desc' : '' }, \
                "INVALID_CCName_Keyvalue" : { 'rc' : '' , 'desc' : '' }, \
                "INVALID_Name_Keyname"    : { 'rc' : '' , 'desc' : '' }, \
                "INVALID_Name_Keyvalue"   : { 'rc' : '' , 'desc' : '' }
              }

def try_invalid_assoc(classname, name_val, i, field):
    j = 0
    keys = {}
    temp = name_val[i]
    name_val[i] = field
    for j in range(len(name_val)/2):
        k = j * 2
        keys[name_val[k]] = name_val[k+1]
    ret_val = try_assoc(conn, classname, ac_classname, keys, field_name=field, \
                              expr_values=expr_values[field], bug_no=bug)
    if ret_val != PASS:
        logger.error("------ FAILED: %s------" % field)
    name_val[i] = temp
    return ret_val


@do_main(sup_types)
def main():
    options = main.options

    log_param()
    status = PASS

    global conn
    conn = assoc.myWBEMConnection('http://%s' % options.ip, (CIM_USER, CIM_PASS), CIM_NS)

    host_name = live.hostname(options.ip)
    host_name_val = [
                        'CreationClassName', 'Xen_HostSystem', \
                        'Name',              host_name
                    ]

    comp_name_val = [
                        'CreationClassName', 'Xen_ComputerSystem', \
                        'Name',              'Domain-0'
                    ]

    tc_scen =       [
                        'INVALID_CCName_Keyname', \
                        'INVALID_CCName_Keyvalue', \
                        'INVALID_Name_Keyname', \
                        'INVALID_Name_Keyvalue'
                    ]

    for i in range(len(tc_scen)):
        retval = try_invalid_assoc('Xen_HostSystem', host_name_val, i, tc_scen[i])
        if retval != PASS:
            status = retval

    for i in range(len(tc_scen)):
        retval = try_invalid_assoc('Xen_ComputerSystem', comp_name_val, i, tc_scen[i])
        if retval != PASS:
            status = retval

    return status
if __name__ == "__main__":
    sys.exit(main())


