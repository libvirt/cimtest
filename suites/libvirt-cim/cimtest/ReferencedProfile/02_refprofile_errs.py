#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <deeptik@linux.vnet.ibm.com>
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
# 
# Test Case Info:
# --------------
# The following test case is used to verify the ReferencedProfile association supported
# returns exceptions when invalid values are passed to it. 
#
# 1) Test by passing Invalid InstanceID Key Name
# Input:
# ------
# wbemcli ai -ac Xen_ReferencedProfile 'http://localhost:5988/root/interop:
# Xen_RegisteredProfile.Wrong="CIM:DSP1042-SystemVirtualization-1.0.0"'  -nl
#
# Output:
# -------
# error code  : CIM_ERR_FAILED 
# error desc  : "No InstanceID specified"
#
# 2) Test by giving invalid Invalid InstanceID Key Value
# Input:
# ------
# wbemcli ain -ac Xen_ReferencedProfile 'http://localhost:5988/root/interop:
# Xen_RegisteredProfile.InstanceID="Wrong"'  -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND 
# error desc  : "No such instance"
#                                          
#  
#                                                          Date : 31-03-2008 

import sys
import pywbem
from XenKvmLib import enumclass
from XenKvmLib import assoc 
from CimTest import Globals
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE, CIM_ERROR_ASSOCIATORS
from CimTest.Globals import do_main, CIM_USER, CIM_PASS
from XenKvmLib.classes import get_typed_class
from CimTest.ReturnCodes import FAIL, PASS, SKIP
from XenKvmLib.common_util import try_assoc
from XenKvmLib.const import CIM_REV

sup_types = ['Xen', 'KVM', 'XenFV']
libvirtcim_rev = 501

expr_values = {
                'INVALID_Instid_KeyName'  :  {
                                                'rc'    : pywbem.CIM_ERR_FAILED, 
                                                'desc'  : "No InstanceID specified"
                                             }, 
                'INVALID_Instid_KeyValue' :  {
                                                'rc'    : pywbem.CIM_ERR_NOT_FOUND,
                                                'desc'  : "No such instance"
                                             }
              }
              

def get_proflist():
    proflist = []
    status = PASS
    try:
        key_list = ["InstanceID"]
        proflist = enumclass.enumerate(server,  reg_classname, key_list, virt)
        if len(proflist) < 5 :
            logger.error("%s returned %i %s objects, expected atleast 5", 
                                           reg_classname, len(proflist), 'Profile')
            status = FAIL

    except Exception, detail:
        logger.error(CIM_ERROR_ENUMERATE, reg_classname)
        logger.error("Exception: %s", detail)
        status = FAIL

    if status != PASS:
        return status, proflist

    profiles_instid_list = [ profile.InstanceID for profile in proflist ]

    return status, profiles_instid_list


def verify_prof_err(field, keys):
    status = PASS
    assoc_classname = get_typed_class(virt, 'ReferencedProfile')
    try:
        ret_value = try_assoc(conn, reg_classname, assoc_classname, keys, field_name=field, \
                                                   expr_values=expr_values[field], bug_no="")
        if ret_value != PASS:
            logger.error("------ FAILED: to verify %s.------", field)
            status = ret_value
    except Exception, detail:
        logger.error(CIM_ERROR_ASSOCIATORS, assoc_classname)
        logger.error("Exception: %s", detail)
        status = FAIL
    return status


@do_main(sup_types)
def main():
    options = main.options
    global virt, server, reg_classname, conn
    virt = options.virt
    server = options.ip
    status = PASS
    # Referenced Profile was introduced as part of changeset 501 
    # and is not available in the libvirt-cim rpm, hence skipping tc
    # if CIM_REV  501
    if CIM_REV < libvirtcim_rev:
        return SKIP

    prev_namespace = Globals.CIM_NS
    Globals.CIM_NS = 'root/interop'
    reg_classname = get_typed_class(virt, 'RegisteredProfile')
    status, proflist = get_proflist()
    if status != PASS :
        Globals.CIM_NS = prev_namespace
        return status 

    conn = assoc.myWBEMConnection('http://%s' % options.ip, (CIM_USER, CIM_PASS),  Globals.CIM_NS)

    for prof in sorted(proflist):
        field = 'INVALID_Instid_KeyName'
        keys = { field : prof }
        status = verify_prof_err(field, keys)
        if status != PASS:
            break

        field = 'INVALID_Instid_KeyValue'
        keys = { 'InstanceID' : field }
        status = verify_prof_err(field, keys)
        if status != PASS:
            break
     
    Globals.CIM_NS = prev_namespace
    return status 

if __name__ == "__main__":
    sys.exit(main())
