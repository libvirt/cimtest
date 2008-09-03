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
# returned by Xen_RCPS on giving invalid inputs.
# 
#         
#                                                        Date : 17-02-2008

import sys
import pywbem
from CimTest.ReturnCodes import PASS
from XenKvmLib import assoc
from CimTest.Globals import logger, CIM_USER, CIM_PASS, CIM_NS
from XenKvmLib.common_util import get_host_info, try_getinstance
from XenKvmLib.const import do_main
from XenKvmLib.classes import get_typed_class

platform_sup = ['Xen', 'KVM', 'XenFV', 'LXC']
expr_values = {
          "invalid_sysname" : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                'desc' : 'No such instance (SystemName)' }, \
          "invalid_sccname" : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                'desc' : 'No such instance \
(SystemCreationClassName)' }, \
          "invalid_name"    : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                'desc' : 'No such instance (Name)' }, \
          "invalid_ccname"  : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                'desc' : 'No such instance (CreationClassName)'}
              }



def err_invalid_ccname_keyname(conn, classname, hostname, sccname, field):
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:\
# Xen_ResourcePoolConfigurationService.Wrong="Xen_ResourcePoolConfigurationService"\
# ,Name="RPCS",SystemCreationClassName="Xen_HostSystem",SystemName="mx3650a.in.ibm.com"'
# 
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND 
# error desc  : "No such instance (CreationClassName)"
#
    keys = { 
             field                     : classname, \
             'Name'                    : 'RPCS', \
             'SystemCreationClassName' : sccname, \
             'SystemName'              : hostname 
           }
    return try_getinstance(conn, classname, keys, field_name=field, \
                           expr_values=expr_values['invalid_ccname'], bug_no="")

def err_invalid_ccname_keyvalue(conn, classname, hostname, sccname, field):
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:\
# Xen_ResourcePoolConfigurationService.CreationClassName="Wrong",\
# Name="RPCS",SystemCreationClassName="Xen_HostSystem",SystemName="mx3650a.in.ibm.com"'
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND 
# error desc  : "No such instance (CreationClassName)"
#
    keys = { 
             'CreationClassName'       : field, \
             'Name'                    : 'RPCS', \
             'SystemCreationClassName' : sccname, \
             'SystemName'              : hostname 
           }
    return try_getinstance(conn, classname, keys, field_name=field, \
                           expr_values=expr_values['invalid_ccname'], bug_no="")

def err_invalid_name_keyname(conn, classname, hostname, sccname, field):
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:\
# Xen_ResourcePoolConfigurationService.CreationClassName=\
# "Xen_ResourcePoolConfigurationService",Wrong="RCPS",\
# SystemCreationClassName="Xen_HostSystem",SystemName="mx3650a.in.ibm.com"'
# 
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (Name)" 
#
    keys = { 
             'CreationClassName'       : classname, \
             field                     : 'RPCS', \
             'SystemCreationClassName' : sccname, \
             'SystemName'              : hostname 
           }
    return try_getinstance(conn, classname, keys, field_name=field, \
                           expr_values=expr_values['invalid_name'], bug_no="")


def err_invalid_name_keyvalue(conn, classname, hostname, sccname, field):
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:\
# Xen_ResourcePoolConfigurationService.CreationClassName=\
# "Xen_ResourcePoolConfigurationService",Name="Wrong",\
# SystemCreationClassName="Xen_HostSystem",SystemName="mx3650a.in.ibm.com"'
# 
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (Name)" 
#
    keys = { 
             'CreationClassName'       : classname, \
             'Name'                    : field, \
             'SystemCreationClassName' : sccname, \
             'SystemName'              : hostname 
           }
    return try_getinstance(conn, classname, keys, field_name=field, \
                           expr_values=expr_values['invalid_name'], bug_no="")


def err_invalid_sccname_keyname(conn, classname, hostname, sccname, field):
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:\
# Xen_ResourcePoolConfigurationService.CreationClassName=\
# "Xen_ResourcePoolConfigurationService",Name="RPCS",\
# Wrong="Xen_HostSystem",SystemName="mx3650a.in.ibm.com"'
# 
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (SystemCreationClassName)"  
#
    keys = { 
             'CreationClassName'       : classname, \
             'Name'                    : 'RPCS', \
             field                     : sccname, \
             'SystemName'              : hostname 
           }
    return try_getinstance(conn, classname, keys, field_name=field, \
                           expr_values=expr_values['invalid_sccname'], 
                           bug_no="")

def err_invalid_sccname_keyvalue(conn, classname, hostname, field):
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:\
# Xen_ResourcePoolConfigurationService.CreationClassName=\
# "Xen_ResourcePoolConfigurationService",Name="RPCS",\
# SystemCreationClassName="Wrong",SystemName="mx3650a.in.ibm.com"'
# 
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (SystemCreationClassName)"  
#
    keys = { 
             'CreationClassName'       : classname, \
             'Name'                    : 'RPCS', \
             'SystemCreationClassName' : field, \
             'SystemName'              : hostname 
           }
    return try_getinstance(conn, classname, keys, field_name=field, \
                           expr_values=expr_values['invalid_sccname'], 
                           bug_no="")

def err_invalid_sysname_keyname(conn, classname, hostname, sccname, field):
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:\
# Xen_ResourcePoolConfigurationService.CreationClassName=\
# "Xen_ResourcePoolConfigurationService",Name="RPCS",\
# SystemCreationClassName="Xen_HostSystem",Wrong="mx3650a.in.ibm.com"'
# 
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (SystemName)"
#
    keys = { 
             'CreationClassName'       : classname, \
             'Name'                    : 'RPCS', \
             'SystemCreationClassName' : sccname, \
             field                     : hostname 
           }
    return try_getinstance(conn, classname, keys, field_name=field, \
                           expr_values=expr_values['invalid_sysname'], 
                           bug_no="")

def err_invalid_sysname_keyvalue(conn, classname, sccname, field):
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:\
# Xen_ResourcePoolConfigurationService.CreationClassName=\
# "Xen_ResourcePoolConfigurationService",Name="RPCS",\
# SystemCreationClassName="Xen_HostSystem",SystemName="Wrong"'
# 
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (SystemName)"
#
    keys = { 
             'CreationClassName'       : classname, \
             'Name'                    : 'RPCS', \
             'SystemCreationClassName' : sccname, \
             'SystemName'              : field 
           }
    return try_getinstance(conn, classname, keys, field_name=field, \
                           expr_values=expr_values['invalid_sysname'], 
                           bug_no="")


@do_main(platform_sup)
def main():
    options = main.options
    status = PASS 
    server = options.ip
    conn = assoc.myWBEMConnection('http://%s' % options.ip, 
                                  (CIM_USER, CIM_PASS), CIM_NS)
    virt = options.virt
    status, hostname, sccname = get_host_info(server, virt)
    if status != PASS:
        logger.error("Problem getting host information")
        return status
    classname = get_typed_class(virt, 'ResourcePoolConfigurationService')
    ret_value = err_invalid_ccname_keyname(conn, classname, hostname, sccname, \
                                                 field='INVALID_CCName_KeyName') 
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid CCName Key Name.------")
        status = ret_value
    ret_value = err_invalid_ccname_keyvalue(conn, classname, hostname, sccname, \
                                            field='INVALID_CCName_KeyValue') 
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid CCName Key Value.------")
        status = ret_value
    ret_value = err_invalid_name_keyname(conn, classname, hostname, sccname, \
                                         field='INVALID_Name_KeyName') 
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid Name Key Name.------")
        status = ret_value
    ret_value = err_invalid_name_keyvalue(conn, classname, hostname, sccname, \
                                          field='INVALID_CCName_KeyValue') 
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid Name Key Value.------")
        status = ret_value
    ret_value = err_invalid_sccname_keyname(conn, classname, hostname, sccname,
                                            field='INVALID_Sys_CCName_KeyName') 
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid System CreationClassName Key Name.------")
        status = ret_value
    ret_value = err_invalid_sccname_keyvalue(conn, classname, hostname, \
                                            field='INVALID_Sys_CCName_KeyValue') 
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid System CreationClassName Key Value.------")
        status = ret_value
    ret_value = err_invalid_sysname_keyname(conn, classname, hostname, sccname,
                                            field='INVALID_SysName_KeyName') 
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid SystemName Key Name.------")
        status = ret_value
    ret_value = err_invalid_sysname_keyvalue(conn, classname, sccname, \
                                             field='INVALID_SysName_KeyValue') 
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid SystemName Key Value.------")
        status = ret_value
    return status
if __name__ == "__main__":
    sys.exit(main())
