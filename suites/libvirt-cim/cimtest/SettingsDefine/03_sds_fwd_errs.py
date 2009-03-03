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
# Verify Xen_SettingsDefineState forward association returns error when invalid
# keyname/keyvalues are supplied
#
# 1. Verify Xen_SettingsDefineState association returns error when invalid
# DeviceID keyname is supplied
#
# Input
# -----
# wbemcli ain -ac Xen_SettingsDefineState 'http://localhost:
# 5988/root/virt:Xen_LogicalDisk.wrong="virt1/xvda",CreationClassName=
# "Xen_LogicalDisk",SystemCreationClassName="Xen_ComputerSystem",SystemName=
# "virt1"' -nl
#
# Output
# ------
# rc   : CIM_ERR_FAILED
# desc : "No DeviceID specified"
#
# 2. Verify Xen_SettingsDefineState association returns error when invalid
# DeviceID keyvalue is supplied
#
# Input
# -----
# wbemcli ain -ac Xen_SettingsDefineState 'http://localhost:
# 5988/root/virt:Xen_LogicalDisk.DeviceID="wrong/xvda",CreationClassName=
# "Xen_LogicalDisk",SystemCreationClassName="Xen_ComputerSystem",SystemName=
# "virt1"' -nl
#
# Output
# ------
# rc   : CIM_ERR_NOT_FOUND
# desc : "No such instance (wrong/xvda)"
#
# 3. Verify Xen_SettingsDefineState association returns error when invalid
# CCName keyname is supplied
#
# Input
# -----
# wbemcli ain -ac Xen_SettingsDefineState 'http://localhost:
# 5988/root/virt:Xen_LogicalDisk.DeviceID="virt1/xvda",wrong=
# "Xen_LogicalDisk",SystemCreationClassName="Xen_ComputerSystem",SystemName=
# "virt1"' -nl
#
# Output
# ------
# rc   : CIM_ERR_NOT_FOUND
# desc : "No such instance (CreationClassName)"
#
# 4. Verify Xen_SettingsDefineState association returns error when invalid
# CCName keyvalue is supplied
#
# Input
# -----
# wbemcli ain -ac Xen_SettingsDefineState 'http://localhost:
# 5988/root/virt:Xen_LogicalDisk.DeviceID="virt1/xvda",CreationClassName=
# "wrong",SystemCreationClassName="Xen_ComputerSystem",SystemName="virt1"' -nl
#
# Output
# ------
# rc   : CIM_ERR_NOT_FOUND
# desc : "No such instance (CreationClassName)"
#
# 5. Verify Xen_SettingsDefineState association returns error when invalid
# SCCName keyname is supplied
#
# Input
# -----
# wbemcli ain -ac Xen_SettingsDefineState 'http://localhost:
# 5988/root/virt:Xen_LogicalDisk.DeviceID="virt1/xvda",CreationClassName=
# "Xen_LogicalDisk",wrong="Xen_ComputerSystem",SystemName="virt1"' -nl
#
# Output
# ------
# rc   : CIM_ERR_NOT_FOUND
# desc : "No such instance (SystemCreationClassName)"
#
# 6. Verify Xen_SettingsDefineState association returns error when invalid
# SCCName keyvalue is supplied
#
# Input
# -----
# wbemcli ain -ac Xen_SettingsDefineState 'http://localhost:
# 5988/root/virt:Xen_LogicalDisk.DeviceID="virt1/xvda",CreationClassName=
# "Xen_LogicalDisk", SystemCreationClassName="wrong",SystemName="virt1"' -nl
#
# Output
# ------
# rc   : CIM_ERR_NOT_FOUND
# desc : "No such instance (SystemCreationClassName)"
#
# 7. Verify Xen_SettingsDefineState association returns error when invalid
# System Name keyname is supplied
#
# Input
# -----
# wbemcli ain -ac Xen_SettingsDefineState 'http://localhost:
# 5988/root/virt:Xen_LogicalDisk.DeviceID="virt1/xvda",CreationClassName=
# "Xen_LogicalDisk",SystemCreationClassName="Xen_ComputerSystem",
# wrong="virt1"' -nl
#
# Output
# ------
# rc   : CIM_ERR_NOT_FOUND
# desc : "No such instance (SystemName)"
#
# 8. Verify Xen_SettingsDefineState association returns error when invalid
# System Name keyvalue is supplied
#
# Input
# -----
# wbemcli ain -ac Xen_SettingsDefineState 'http://localhost:
# 5988/root/virt:Xen_LogicalDisk.DeviceID="virt1/xvda",CreationClassName=
# "Xen_LogicalDisk",SystemCreationClassName="Xen_ComputerSystem",SystemName=
# "wrong"' -nl
#
# Output
# ------
# rc   : CIM_ERR_NOT_FOUND
# desc : "No such instance (SystemName)"
#
#                                                Date : 05-03-2008

import sys
import pywbem
from XenKvmLib import assoc
from XenKvmLib import vxml
from XenKvmLib.common_util import try_assoc
from XenKvmLib.classes import get_typed_class
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import logger, CIM_USER, CIM_PASS, CIM_NS
from XenKvmLib.const import do_main, get_provider_version

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom = "domu1"
test_mac = "00:11:22:33:44:aa"
test_vcpus = 1

expr_values = {
    "INVALID_DevID_Keyname"   : { 'rc'   : pywbem.CIM_ERR_FAILED, 
                     'desc' : 'No DeviceID specified' }, 
    "INVALID_DevID_Keyval"    : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, 
                     'desc' : 'No such instance (bad id INVALID_DevID_Keyval)'}, 
    "INVALID_CCName_Keyname"  : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, 
                     'desc' : 'No such instance (CreationClassName)'}, 
    "INVALID_CCName_Keyval"   : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, 
                     'desc' : 'No such instance (CreationClassName)'}, 
    "INVALID_SCCName_Keyname" : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, 
                     'desc' : 'No such instance (SystemCreationClassName)'}, 
    "INVALID_SCCName_Keyval"  : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, 
                     'desc' : 'No such instance (SystemCreationClassName)'}, 
    "INVALID_SysName_Keyname" : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, 
                     'desc' : 'No such instance (SystemName)'}, 
    "INVALID_SysName_Keyval"  : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, 
                     'desc' : 'No such instance (SystemName)'}
}

def get_name_val(classname, device_id, sccn):
    devid = "%s/%s" % (test_dom, device_id)
    name_val = [
                'DeviceID'                , devid, 
                'CreationClassName'       , classname, 
                'SystemCreationClassName' , sccn, 
                'SystemName'              , test_dom
               ]
    return name_val

def try_invalid_assoc(classname, name_val, i, field, virt):
    keys = {}
    temp = name_val[i]
    name_val[i] = field
    for j in range(len(name_val)/2):
        k = j * 2
        keys[name_val[k]] = name_val[k+1]
    ac_classname = get_typed_class(virt, 'SettingsDefineState')
    ret_val = try_assoc(conn, classname, ac_classname, keys, field_name=field, 
                        expr_values=expr_values[field], bug_no='')
    if ret_val != PASS:
        logger.error("------ FAILED: %s------", field)
    name_val[i] = temp
    return ret_val

@do_main(sup_types)
def main():
    options = main.options
    status = PASS

    if options.virt == 'Xen':
        test_disk = 'xvda'
    else:
        test_disk = 'hda'

    virt_xml = vxml.get_class(options.virt)
    if options.virt == 'LXC':
        cxml = virt_xml(test_dom)
    else:
        cxml= virt_xml(test_dom, vcpus = test_vcpus, mac = test_mac,
                       disk = test_disk)

    ret = cxml.cim_define(options.ip)
    if not ret:
        logger.error("Failed to define the dom: %s", test_dom)
        return FAIL

    status = cxml.cim_start(options.ip)
    if status != PASS:
        cxml.undefine(options.ip)
        logger.error("Failed to start the dom: %s", test_dom)
        return FAIL

    global conn
    conn = assoc.myWBEMConnection('http://%s' % options.ip, (CIM_USER, 
                                  CIM_PASS), CIM_NS)
    if options.virt == 'LXC':
        class_id = {get_typed_class(options.virt, 'Memory')      : 'mem'}
    else:
        class_id = {
                    get_typed_class(options.virt, 'LogicalDisk') : test_disk,
                    get_typed_class(options.virt, 'Memory')      : 'mem',
                    get_typed_class(options.virt, 'NetworkPort') : test_mac,
                    get_typed_class(options.virt, 'Processor')   : test_vcpus - 1
                   }

    tc_scen = [
                'INVALID_DevID_Keyname',   'INVALID_DevID_Keyval', 
                'INVALID_CCName_Keyname',  'INVALID_CCName_Keyval', 
                'INVALID_SCCName_Keyname', 'INVALID_SCCName_Keyval', 
                'INVALID_SysName_Keyname', 'INVALID_SysName_Keyval'
              ]

    rev, changeset = get_provider_version(options.virt, options.ip)
    if rev < 682:
        old_ret = { 'rc' : pywbem.CIM_ERR_NOT_FOUND,
                    'desc' : "No such instance (INVALID_DevID_Keyval)"
                  }
        expr_values["INVALID_DevID_Keyval"] = old_ret

    sccn = get_typed_class(options.virt, 'ComputerSystem')
    for classname, devid in sorted(class_id.items()):
        name_val = get_name_val(classname, devid, sccn)
        for i in range(len(tc_scen)):
            retval = try_invalid_assoc(classname, name_val, i,
                                       tc_scen[i], options.virt)
            if retval != PASS:
                status = retval

    cxml.cim_destroy(options.ip)
    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())


