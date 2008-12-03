#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Author:
#   Anoop V Chakkalakkal
#   Guolian Yun <yunguol@cn.ibm.com>
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
# returned by Xen_NetworkPort on giving invalid inputs.
#
#
#                                                        Date : 18-02-2008

import sys
import pywbem
from VirtLib import utils
from XenKvmLib import assoc
from XenKvmLib.common_util import try_getinstance
from XenKvmLib.classes import get_typed_class
from XenKvmLib.vxml import XenXML, KVMXML, LXCXML, get_class
from CimTest.ReturnCodes import PASS, SKIP
from CimTest.Globals import logger, CIM_USER, CIM_PASS, CIM_NS
from XenKvmLib.const import do_main

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']


expr_values = {
                "invalid_sysname" : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                      'desc' : 'No such instance'}, \
                "invalid_sccname" : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                      'desc' : 'No such instance'}, \
                "invalid_devid"   : { 'rc'   : pywbem.CIM_ERR_FAILED, \
                                      'desc' : 'No DeviceID specified'}, \
                "invalid_ccname"  : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                      'desc' : 'No such instance'}
              }

def err_invalid_ccname_keyname():
# Input:
# ------
# wbemcli gi '<scheme>://[user:pwd@]<host>:<port>/<namespace:Xen_NetworkPort.
# DeviceID="<deviceid>",
# SystemCreationClassName="Xen_ComputerSystem",
# SystemName="<sys name>"'
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (CreationClassName)"
#
    keys = {
             'DeviceID'                : devid, \
             'SystemCreationClassName' : sccname, \
             'SystemName'              : guestname
           }
    return try_getinstance(conn, classname, keys, 
                           field_name='INVALID_CCName_KeyName', \
                           expr_values=expr_values['invalid_ccname'], bug_no="")


def err_invalid_ccname_keyvalue():
# Input:
# ------
# wbemcli gi '<scheme>://[user:pwd@]<host>:<port>/<namespace:Xen_NetworkPort.
# CreationClassName="",
# DeviceID="<deviceid>",
# SystemCreationClassName="Xen_ComputerSystem",
# SystemName="<sys name>"'
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (CreationClassName)"
#
    keys = {
             'CreationClassName'       : '', \
             'DeviceID'                : devid, \
             'SystemCreationClassName' : sccname, \
             'SystemName'              : guestname
           }
    return try_getinstance(conn, classname, keys, 
                           field_name='INVALID_CCName_KeyValue', \
                           expr_values=expr_values['invalid_ccname'], bug_no="")

def err_invalid_devid_keyname():
# Input:
# ------
# wbemcli gi '<scheme>://[user:pwd@]<host>:<port>/<namespace:Xen_NetworkPort.
# CreationClassName="Xen_NetworkPort",
# SystemCreationClassName="Xen_ComputerSystem",
# SystemName="<sys name>"'
#
# Output:
# -------
# error code  : CIM_ERR_FAILED
# error desc  : "No DeviceID specified"
#
    keys = {
             'CreationClassName'       : classname, \
             'SystemCreationClassName' : sccname, \
             'SystemName'              : guestname
           }
    return try_getinstance(conn, classname, keys, 
                           field_name='INVALID_DevID_KeyName', \
                           expr_values=expr_values['invalid_devid'], bug_no="")


def err_invalid_devid_keyvalue():
# Input:
# ------
# wbemcli gi '<scheme>://[user:pwd@]<host>:<port>/<namespace:Xen_NetworkPort.
# CreationClassName="Xen_NetworkPort",
# DeviceID="",
# SystemCreationClassName="Xen_ComputerSystem",
# SystemName="<sys name>"'
#
# Output:
# -------
# error code  : CIM_ERR_FAILED
# error desc  : "No DeviceID specified"
#
    keys = {
             'CreationClassName'       : classname, \
             'DeviceID'                : '', \
             'SystemCreationClassName' : sccname, \
             'SystemName'              : guestname
           }
    return try_getinstance(conn, classname, keys, 
                           field_name='INVALID_DevID_KeyValue', \
                           expr_values=expr_values['invalid_devid'], bug_no="")


def err_invalid_sccname_keyname():
# Input:
# ------
# wbemcli gi '<scheme>://[user:pwd@]<host>:<port>/<namespace:Xen_NetworkPort.
# CreationClassName="Xen_NetworkPort",
# DeviceID="<deviceid>",
# SystemName="<sys name>"'
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (SystemCreationClassName)"
#
    keys = {
             'CreationClassName'       : classname, \
             'DeviceID'                : devid, \
             'SystemName'              : guestname
           }
    return try_getinstance(conn, classname, keys, 
                          field_name='INVALID_Sys_CCName_KeyName', \
                          expr_values=expr_values['invalid_sccname'], bug_no="")

def err_invalid_sccname_keyvalue():
# Input:
# ------
# wbemcli gi '<scheme>://[user:pwd@]<host>:<port>/<namespace:Xen_NetworkPort.
# CreationClassName="Xen_NetworkPort",
# DeviceID="<deviceid>",
# SystemCreationClassName="",
# SystemName="<sys name>"'
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (SystemCreationClassName)"
#
    keys = {
             'CreationClassName'       : classname, \
             'DeviceID'                : devid, \
             'SystemCreationClassName' : '', \
             'SystemName'              : guestname
           }
    return try_getinstance(conn, classname, keys, 
                          field_name='INVALID_Sys_CCName_KeyValue', \
                          expr_values=expr_values['invalid_sccname'], bug_no="")

def err_invalid_sysname_keyname():
# Input:
# ------
# wbemcli gi '<scheme>://[user:pwd@]<host>:<port>/<namespace:Xen_NetworkPort.
# CreationClassName="Xen_NetworkPort",
# DeviceID="<deviceid>",
# SystemCreationClassName="Xen_ComputerSystem"'
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (SystemName)"
#
    keys = {
             'CreationClassName'       : classname, \
             'DeviceID'                : devid, \
             'SystemCreationClassName' : sccname, \
           }
    return try_getinstance(conn, classname, keys, 
                          field_name='INVALID_SysName_KeyName', \
                          expr_values=expr_values['invalid_sysname'], bug_no="")

def err_invalid_sysname_keyvalue():
# Input:
# ------
# wbemcli gi '<scheme>://[user:pwd@]<host>:<port>/<namespace:Xen_NetworkPort.
# CreationClassName="Xen_NetworkPort",
# DeviceID="<deviceid>",
# SystemCreationClassName="Xen_ComputerSystem",
# SystemName=""'
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "No such instance (SystemName)"
#
    keys = {
             'CreationClassName'       : classname, \
             'DeviceID'                : devid, \
             'SystemCreationClassName' : sccname, \
             'SystemName'              : ''
           }
    return try_getinstance(conn, classname, keys, 
                          field_name='INVALID_SysName_KeyValue', \
                          expr_values=expr_values['invalid_sysname'], bug_no="")

@do_main(sup_types)
def main():
    options = main.options
    status = PASS

    test_dom = "nettest_domain"
    test_mac = "00:11:22:33:44:55"
   
    vsxml = get_class(options.virt)(test_dom, mac=test_mac)
    ret = vsxml.cim_define(options.ip)
    if ret != 1:
        logger.error("Define domain failed!")
        return SKIP
    
    global conn
    global classname
    global guestname
    global sccname
    global devid
    
    conn = assoc.myWBEMConnection('http://%s' % options.ip, (CIM_USER, CIM_PASS), CIM_NS)    
    classname = get_typed_class(options.virt, 'NetworkPort')
    guestname = test_dom
    sccname = get_typed_class(options.virt, 'ComputerSystem')
    devid = "%s/%s" % (test_dom, test_mac)

    ret_value = err_invalid_ccname_keyname()
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid CCName Key Name.------")
        status = ret_value

    ret_value = err_invalid_ccname_keyvalue()
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid CCName Key Value.------")
        status = ret_value

    ret_value = err_invalid_devid_keyname()
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid DeviceID Key Name.------")
        status = ret_value

    ret_value = err_invalid_devid_keyvalue()
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid DeviceID Key Value.------")
        status = ret_value

    ret_value = err_invalid_sccname_keyname()
    if ret_value != PASS:
        logger.error("---FAILED: Invalid System CreationClassName Key Name.---")
        status = ret_value

    ret_value = err_invalid_sccname_keyvalue()
    if ret_value != PASS:
        logger.error("--FAILED: Invalid System CreationClassName Key Value.--")
        status = ret_value

    ret_value = err_invalid_sysname_keyname()
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid SystemName Key Name.------")
        status = ret_value

    ret_value = err_invalid_sysname_keyvalue()
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid SystemName Key Value.------")
        status = ret_value

    vsxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())
