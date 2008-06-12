#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Author:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
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
# This tc is used to verify if appropriate exceptions are 
# returned by Xen_SettingsDefineCapabilities asscoiation 
# on giving invalid inputs.
# 
#         
#                                                        Date : 17-02-2008

import sys
import pywbem
from CimTest.ReturnCodes import PASS
from XenKvmLib.common_util import try_assoc
from XenKvmLib import assoc
from CimTest.Globals import logger, CIM_USER, CIM_PASS, CIM_NS
from CimTest.Globals import do_main, platform_sup
from XenKvmLib.classes import get_typed_class

expr_values = {
   "invalid_instid_keyname"  : { 'rc'   : pywbem.CIM_ERR_FAILED, 
                                 'desc' : 'Missing InstanceID'},
   "invalid_instid_keyvalue" : { 'rc' : pywbem.CIM_ERR_FAILED, 
                                 'desc' : 'Unable to determine\
 resource type' },
   "invalid_ccname_keyname"  : { 'rc'   : pywbem.CIM_ERR_INVALID_PARAMETER, 
                                 'desc' : 'CIM_ERR_INVALID_PARAMETER' }
              }

def err_invalid_instid_keyname(virt, conn, field):
# Input:
# ------
# wbemcli ai -ac Xen_SettingsDefineCapabilities \
# 'http://localhost:5988/root/virt:Xen_AllocationCapabilities.\
# wrong="ProcessorPool/0"' -nl
#
# Output:
# -------
# error code  : CIM_ERR_FAILED
# error desc  : "Missing InstanceID"
#
    assoc_classname = get_typed_class(virt, "SettingsDefineCapabilities")
    classname = get_typed_class(virt, "AllocationCapabilities")
    keys = { field : 'MemoryPool/0' }
    return try_assoc(conn, classname, assoc_classname, keys, field_name=field, \
                     expr_values=expr_values['invalid_instid_keyname'], 
                     bug_no="")

def err_invalid_instid_keyvalue(virt, conn, field):
# Input:
# ------
# wbemcli ai -ac Xen_SettingsDefineCapabilities \
# 'http://localhost:5988/root/virt:Xen_AllocationCapabilities.\
# InstanceID="wrong/0"' -nl
# 
# Output:
# -------
# Verify for the error
# error code  : CIM_ERR_FAILED
# error desc  : "Unable to determine resource type"
    assoc_classname = get_typed_class(virt, "SettingsDefineCapabilities")
    classname = get_typed_class(virt, "AllocationCapabilities")
    keys = { 'InstanceID' : field }
    return try_assoc(conn, classname, assoc_classname, keys, field_name=field, \
                     expr_values=expr_values['invalid_instid_keyvalue'], 
                     bug_no="")

def err_invalid_ccname_keyname(virt, conn, field):
# Input:
# ------
# wbemcli ai -ac Xen_SettingsDefineCapabilities \
# 'http://localhost:5988/root/virt:Wrong.InstanceID="ProcessorPool/0"' -nl
#
# Output:
# -------
# error code    : CIM_ERR_INVALID_PARAMETER
# error desc    : One or more parameter values passed to the method were invalid
    assoc_classname = get_typed_class(virt, "SettingsDefineCapabilities")
    classname = field
    keys = { 'InstanceID' : 'MemoryPool/0' }
    return try_assoc(conn, classname, assoc_classname, keys, field_name=field, \
                     expr_values=expr_values['invalid_ccname_keyname'],
                     bug_no="")

@do_main(platform_sup)
def main():
    options = main.options
    virt = options.virt
    conn = assoc.myWBEMConnection('http://%s' % options.ip, 
                                  (CIM_USER, CIM_PASS), CIM_NS)
    ret_value = err_invalid_instid_keyname(virt, conn, 
                                           field='INVALID_InstID_KeyName')
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid InstanceID Key Name.------")
        return ret_value
    ret_value = err_invalid_instid_keyvalue(virt, conn, 
                                            field='INVALID_InstID_KeyValue')
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid InstanceID Key Value.------")
        return ret_value
    ret_value = err_invalid_ccname_keyname(virt, conn, field='WrongClassName')
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid CCName Key Name.------")
        return ret_value
    return PASS
    
if __name__ == "__main__":
    sys.exit(main())
