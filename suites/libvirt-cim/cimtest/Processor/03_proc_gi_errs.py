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
# 1) Test by passing Invalid CCName Keyname
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:Xen_Processor.\
# wrong="Xen_Processor",DeviceID="Domain-0/0",SystemCreationClassName=\
# "Xen_ComputerSystem",SystemName="Domain-0"' -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (CreationClassName)"

# 2) Test by passing Invalid CCName Keyvalue
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:Xen_Processor.\
# CreationClassName="wrong",DeviceID="Domain-0/0",SystemCreationClassName=\
# "Xen_ComputerSystem",SystemName="Domain-0"' -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (CreationClassName)"

# 3) Test by passing Invalid DevId Keyname
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:Xen_Processor.\
# CreationClassName="Xen_Processor",wrong="Domain-0/0",SystemCreationClassName=\
# "Xen_ComputerSystem",SystemName="Domain-0"' -nl
#
# Output:
# -------
# error code  : CIM_ERR_FAILED
# error desc  : "No DeviceID specified"

# 4) Test by passing Invalid DevId Keyvalue
# ------
# wbemcli gi 'http://localhost:5988/root/virt:Xen_Processor.\
# CreationClassName="Xen_Processor",DeviceID="wrong",SystemCreationClassName=\
# "Xen_ComputerSystem",SystemName="Domain-0"' -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (wrong)"

# 5) Test by passing Invalid SCCName Keyname
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:Xen_Processor.\
# CreationClassName="Xen_Processor",DeviceID="Domain-0/0",wrong=\
# "Xen_ComputerSystem",SystemName="Domain-0"' -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (SystemCreationClassName)"

# 6) Test by passing Invalid SCCName Keyvalue
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:Xen_Processor.\
# CreationClassName="Xen_Processor",DeviceID="Domain-0/0",SystemCreationClassName=\
# "wrong",SystemName="Domain-0"' -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (SystemCreationClassName)"

# 7) Test by passing Invalid SysName Keyname
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:Xen_Processor.\
# CreationClassName="Xen_Processor",DeviceID="Domain-0/0",SystemCreationClassName=\
# "Xen_ComputerSystem",wrong="Domain-0"' -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (SystemName)"

# 8) Test by passing Invalid SysName Keyvalue# Input:
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:Xen_Processor.\
# CreationClassName="Xen_Processor",DeviceID="Domain-0/0",SystemCreationClassName=\
# "Xen_ComputerSystem",SystemName="wrong"' -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (SystemName)"
#                                                   -Date 26.02.2008

import sys
import pywbem
from XenKvmLib import assoc
from XenKvmLib.common_util import try_getinstance
from XenKvmLib.classes import get_typed_class
from XenKvmLib.vxml import get_class
from XenKvmLib.test_doms import destroy_and_undefine_all
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import logger, CIM_USER, CIM_PASS, CIM_NS
from XenKvmLib.const import do_main, get_provider_version

sup_types = ['Xen', 'KVM', 'XenFV']

expr_values = {
    "invalid_ccname"         : {'rc'   : pywbem.CIM_ERR_NOT_FOUND, 
                                'desc' : "No such instance (CreationClassName)" }, 
    "invalid_devid_keyname"  : {'rc'   : pywbem.CIM_ERR_FAILED, 
                                'desc' : "No DeviceID specified" }, 
    "invalid_devid_keyvalue" : {'rc'   : pywbem.CIM_ERR_NOT_FOUND, 
                                'desc' : "No such instance "\
                                         "(bad id INVALID_DevID_Keyvalue)" }, 
    "invalid_sccname"        : {'rc'   : pywbem.CIM_ERR_NOT_FOUND, 
                                'desc' : "No such instance (SystemCreationClassName)" }, 
    "invalid_sysname"        : {'rc'   : pywbem.CIM_ERR_NOT_FOUND, 
                                'desc' : "No such instance (SystemName)" }
              }

test_dom = "proc_domain"
test_vcpus = 1


def try_invalid_gi(i, field1, field2):
    j = 0
    keys = {}
    temp = name_val[i]
    name_val[i] = field1
    for j in range(len(name_val)/2):
        k = j * 2
        keys[name_val[k]] = name_val[k+1]

    ret_value = try_getinstance(conn, classname, keys, field_name=field1, 
                                expr_values=expr_values[field2], bug_no="")
    if ret_value != PASS:
        logger.error("------ FAILED: %s------" % field1)
    name_val[i] = temp
    return ret_value

@do_main(sup_types)
def main():
    options = main.options

    devid = "%s/%s" % (test_dom, "0")
    status = PASS

    # Getting the VS list and deleting the test_dom if it already exists.
    destroy_and_undefine_all(options.ip)
    vsxml = get_class(options.virt)(test_dom, vcpus=test_vcpus)
    vsxml.cim_define(options.ip)
    ret = vsxml.start(options.ip)
    if not ret:
        logger.error("Failed to Create the dom: %s", test_dom)
        return FAIL
    global conn
    conn = assoc.myWBEMConnection('http://%s' % options.ip, (CIM_USER, CIM_PASS), CIM_NS)

    global name_val
    global classname 
    classname = get_typed_class(options.virt, 'Processor')
    name_val = [
                'CreationClassName',       classname, 
                'DeviceID',                devid, 
                'SystemCreationClassName', get_typed_class(options.virt, 'ComputerSystem'), 
                'SystemName',              test_dom
              ]

    tc_scen = { 'INVALID_CCName_Keyname'   : 'invalid_ccname', 
                'INVALID_CCName_Keyvalue'  : 'invalid_ccname', 
                'INVALID_DevID_Keyname'    : 'invalid_devid_keyname', 
                'INVALID_DevID_Keyvalue'   : 'invalid_devid_keyvalue', 
                'INVALID_SCCName_Keyname'  : 'invalid_sccname', 
                'INVALID_SCCName_Keyvalue' : 'invalid_sccname', 
                'INVALID_SysName_Keyname'  : 'invalid_sysname', 
                'INVALID_SysName_Keyvalue' : 'invalid_sysname'
              }

    rev, changeset = get_provider_version(options.virt, options.ip)
    if rev < 682:
        old_ret = { 'rc' : pywbem.CIM_ERR_NOT_FOUND,
                    'desc' : "No such instance (INVALID_DevID_Keyvalue)"
                  }
        expr_values["invalid_devid_keyvalue"] = old_ret

    i = 0
    for field1, field2 in sorted(tc_scen.items()):
        retval = try_invalid_gi(i, field1, field2)
        if retval != PASS:
            status = retval
        i = i + 1

    vsxml.destroy(options.ip)
    vsxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())
