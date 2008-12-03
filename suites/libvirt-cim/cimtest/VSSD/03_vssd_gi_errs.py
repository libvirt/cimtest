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
# Test Case Info:
# --------------
# This tc is used to verify if appropriate exceptions are
# returned by Xen_VirtualSystemSettingData on giving invalid inputs.
#
# 1) Test by passing Invalid InstID Keyname
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:\
# Xen_VirtualSystemSettingData.INVALID_InstID_Keyname="Xen:new"' -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (InstanceID)"

# 2) Test by passing Invalid InstID Keyvalue
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:\
# Xen_VirtualSystemSettingData.InstanceID="INVALID_InstID_Keyval"' -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (InstanceID)"
#
#                                                   Date: 06-03-2008

import sys
import pywbem
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.const import do_main
from CimTest.Globals import CIM_PASS, CIM_NS, CIM_USER, logger
from XenKvmLib import assoc
from XenKvmLib.vxml import get_class
from XenKvmLib.common_util import try_getinstance
from XenKvmLib.test_doms import destroy_and_undefine_all

platform_sup = ['Xen', 'KVM', 'XenFV', 'LXC']
test_dom  = "VSSD_domain"

expr_values = {
    "INVALID_InstID_Keyname"   : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                     'desc' : 'No such instance (InstanceID)' }, \
    "INVALID_InstID_Keyval"    : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                     'desc' : 'No such instance (InstanceID)'}
}

def try_invalid_gi(VSType, name_val, i, field):
    classname = "%s_VirtualSystemSettingData" % VSType
    keys = {}
    temp = name_val[i]
    name_val[i] = field
    for j in range(len(name_val)/2):
        k = j * 2
        keys[name_val[k]] = name_val[k+1]
    ret_val = try_getinstance(conn, classname, keys, field_name=field, \
                             expr_values=expr_values[field], bug_no="")
    if ret_val != PASS:
        logger.error("------ FAILED: %s ------", field)
    name_val[i] = temp
    return ret_val

@do_main(platform_sup)
def main():
    options = main.options
    status = PASS
    if options.virt == 'XenFV':
        VSType = 'Xen' 
    else:
        VSType = options.virt
    vsxml = get_class(options.virt)(test_dom)
    ret = vsxml.cim_define(options.ip)
    if not ret :
        logger.error("error while define of VS")
        return FAIL

    global conn
    conn = assoc.myWBEMConnection('http://%s' % options.ip, (CIM_USER, CIM_PASS), CIM_NS)

    inst_id  = "%s:%s" % (VSType, test_dom)
    name_val = ['InstanceID', inst_id]
    tc_scen  = ['INVALID_InstID_Keyname', 'INVALID_InstID_Keyval']

    for i in range(len(tc_scen)):
        retval = try_invalid_gi(VSType, name_val, i, tc_scen[i])
        if retval != PASS:
            status = retval

    vsxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())

