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
from VirtLib import utils
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import logger, do_main
from CimTest.Globals import CIM_PASS, CIM_NS, CIM_USER
from XenKvmLib import assoc
from XenKvmLib.test_xml import testxml
from XenKvmLib.common_util import try_getinstance
from XenKvmLib.test_doms import test_domain_function, destroy_and_undefine_all

sup_types = ['Xen']

VSType    = "Xen"
test_dom  = "new"
classname = "Xen_VirtualSystemSettingData"

expr_values = {
    "INVALID_InstID_Keyname"   : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                     'desc' : 'No such instance (InstanceID)' }, \
    "INVALID_InstID_Keyval"    : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                     'desc' : 'No such instance (InstanceID)'}
}

def try_invalid_gi(name_val, i, field):
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

@do_main(sup_types)
def main():
    options = main.options
    if not options.ip:
        parser.print_help()
        return FAIL

    status = PASS

    destroy_and_undefine_all(options.ip)
    xmlfile = testxml(test_dom )

    ret = test_domain_function(xmlfile, options.ip, "define")
    if not ret :
        logger.error("error while define of VS")
        return FAIL

    global conn
    conn = assoc.myWBEMConnection('http://%s' % options.ip, (CIM_USER,
CIM_PASS), CIM_NS)

    inst_id  = "%s:%s" % (VSType, test_dom)
    name_val = ['InstanceID', inst_id]
    tc_scen  = ['INVALID_InstID_Keyname', 'INVALID_InstID_Keyval']

    for i in range(len(tc_scen)):
        retval = try_invalid_gi(name_val, i, tc_scen[i])
        if retval != PASS:
            status = retval

    test_domain_function(test_dom, options.ip, "undefine")
    return status

if __name__ == "__main__":
    sys.exit(main())

