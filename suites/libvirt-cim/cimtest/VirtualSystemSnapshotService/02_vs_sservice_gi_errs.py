#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B.Kalakeri 
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
# returned by VirtualSystemSnapshotService on giving invalid inputs.
# 
#                                                         Date: 24-03-2008
import sys
import pywbem
from XenKvmLib import assoc
from CimTest.Globals import log_param, logger, CIM_USER, CIM_PASS, CIM_NS
from CimTest.ReturnCodes import PASS
from XenKvmLib.common_util import try_getinstance
from CimTest.Globals import do_main, platform_sup
from XenKvmLib.classes import get_typed_class
from XenKvmLib.common_util import get_host_info

expr_values = {
                "INVALID_CCName"    :  { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                          'desc' : 'No such instance (CreationClassName)' }, \
                "INVALID_Name"      :  { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                          'desc' : 'No such instance (Name)' }, \
                "INVALID_SCCName"   :  { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                          'desc' : 'No such instance (SystemCreationClassName)'}, \
                "INVALID_SName"     :  { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                          'desc' : 'No such instance (SystemName)' }, 
              }


def verify_fields(keys):
    classname = get_typed_class(options.virt, "VirtualSystemSnapshotService") 
    return try_getinstance(conn, classname, keys, field_name=field, \
                                 expr_values=expr_values[field], bug_no="")

def err_invalid_ccname():
# 1) Test by giving invalid CreationClassName Key Name
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:KVM_VirtualSystemSnapshotService. \
# Wrong="KVM_VirtualSystemSnapshotService",Name="SnapshotService",\
# SystemCreationClassName="KVM_HostSystem",SystemName="mx3650a.in.ibm.com"' -nl
#
# 2) Test by passing Invalid CreationClassName Key Value
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:KVM_VirtualSystemSnapshotService. \
# CreationClassName="Wrong",Name="SnapshotService",\
# SystemCreationClassName="KVM_HostSystem",SystemName="mx3650a.in.ibm.com"' -nl
# 
# Inboth the cases the following exception is verified.
# 
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND 
# error desc  :  "No such instance (CreationClassName)" 
    keys = { field                     : ccn,  \
             'Name'                    : name, \
             'SystemCreationClassName' : sccn, \
             'SystemName'              : sys_name
           }
    status = verify_fields(keys)
    if status != PASS:
        logger.error("------ FAILED: to check INVALID_CCName_KeyName.------")
        return status
    keys = { 'CreationClassName'       : field, \
             'Name'                    : name,  \
             'SystemCreationClassName' : sccn,  \
             'SystemName'              : sys_name
           }
    status = verify_fields(keys)
    if status != PASS:
        logger.error("------ FAILED: to check INVALID_CCName_KeyValue.------")
        return status
    return PASS

def err_invalid_name():
# 1) Test by giving invalid Name Key Name
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:KVM_VirtualSystemSnapshotService. \
# CreationClassName="KVM_VirtualSystemSnapshotService",Wrong="SnapshotService",\
# SystemCreationClassName="KVM_HostSystem",SystemName="mx3650a.in.ibm.com"' -nl
#
# 2) Test by passing Invalid CreationClassName Key Value
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:KVM_VirtualSystemSnapshotService. \
# CreationClassName="KVM_VirtualSystemSnapshotService",Name="Wrong",\
# SystemCreationClassName="KVM_HostSystem",SystemName="mx3650a.in.ibm.com"' -nl
# 
# Inboth the cases the following exception is verified.
# 
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND 
# error desc  :  "No such instance (Name)" 
#
    keys = { 'CreationClassName'       : ccn,  \
              field                    : name, \
             'SystemCreationClassName' : sccn, \
             'SystemName'              : sys_name
           }
    status = verify_fields(keys)
    if status != PASS:
        logger.error("------ FAILED: to check INVALID_Name_KeyName.------")
        return status
    keys = { 'CreationClassName'       : ccn,   \
             'Name'                    : field, \
             'SystemCreationClassName' : sccn,  \
             'SystemName'              : sys_name
           }
    status = verify_fields(keys)
    if status != PASS:
        logger.error("------ FAILED: to check INVALID_Name_KeyValue.------")
        return status
    return PASS

def err_invalid_sccname():
# 1) Test by giving invalid SystemCreationClassName Key Name
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:KVM_VirtualSystemSnapshotService. \
# CreationClassName="KVM_VirtualSystemSnapshotService",Name="SnapshotService",\
# Wrong="KVM_HostSystem",SystemName="mx3650a.in.ibm.com"' -nl
#
# 2) Test by passing Invalid CreationClassName Key Value
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:KVM_VirtualSystemSnapshotService. \
# CreationClassName="KVM_VirtualSystemSnapshotService",Name="SnapshotService",\
# SystemCreationClassName="Wrong",SystemName="mx3650a.in.ibm.com"' -nl
# 
# Inboth the cases the following exception is verified.
# 
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND 
# error desc  :  "No such instance (SystemCreationClassName)" 
#
    keys = { 'CreationClassName'       : ccn,  \
             'Name'                    : name, \
             field                     : sccn, \
             'SystemName'              : sys_name
           }
    status = verify_fields(keys)
    if status != PASS:
        logger.error("------ FAILED: to check INVALID_SCCName_KeyName.------")
        return status
    keys = { 'CreationClassName'       : ccn,   \
             'Name'                    : name, \
             'SystemCreationClassName' : field,  \
             'SystemName'              : sys_name
           }
    status = verify_fields(keys)
    if status != PASS:
        logger.error("------ FAILED: to check INVALID_SCCName_KeyValue.------")
        return status
    return PASS

def err_invalid_sname():
# 1) Test by giving invalid SystemName Key Name
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:KVM_VirtualSystemSnapshotService. \
# CreationClassName="KVM_VirtualSystemSnapshotService",Name="SnapshotService",\
# SystemCreationClassName="KVM_HostSystem",Wrong="mx3650a.in.ibm.com"' -nl
#
# 2) Test by passing Invalid CreationClassName Key Value
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:KVM_VirtualSystemSnapshotService. \
# CreationClassName="KVM_VirtualSystemSnapshotService",Name="SnapshotService",\
# SystemCreationClassName="KVM_HostSystem",SystemName="Wrong"' -nl
# 
# Inboth the cases the following exception is verified.
# 
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND 
# error desc  :  "No such instance (SystemName)" 
#
    keys = { 'CreationClassName'       : ccn,  \
             'Name'                    : name, \
             'SystemCreationClassName' : sccn, \
             field                     : sys_name
           }
    status = verify_fields(keys)
    if status != PASS:
        logger.error("------ FAILED: to check INVALID_SName_KeyName.------")
        return status
    keys = { 'CreationClassName'       : ccn,   \
             'Name'                    : name, \
             'SystemCreationClassName' : sccn,  \
             'SystemName'              : field
           }
    status = verify_fields(keys)
    if status != PASS:
        logger.error("------ FAILED: to check INVALID_SName_KeyValue.------")
        return status
    return PASS

@do_main(platform_sup)
def main():
    global options
    options = main.options
    log_param()
    global conn
    global field
    global ccn 
    global name, sys_name, sccn
    conn = assoc.myWBEMConnection('http://%s' % options.ip, (CIM_USER, CIM_PASS), CIM_NS)
    ccn  = get_typed_class(options.virt, "VirtualSystemSnapshotService")
    name = "SnapshotService"
    status, sys_name, sccn = get_host_info(options.ip, options.virt)
    if status != PASS:
        return status
    field = 'INVALID_CCName'
    status = err_invalid_ccname()
    if status != PASS:
        return status
    field = 'INVALID_Name'
    status = err_invalid_name()
    if status != PASS:
        return status
    field = 'INVALID_SCCName'
    status = err_invalid_sccname()
    if status != PASS:
        return status
    field = 'INVALID_SName'
    status = err_invalid_sname()
    if status != PASS:
        return status
    return PASS
if __name__ == "__main__":
    sys.exit(main())
