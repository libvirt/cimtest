#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Anoop V Chakkalakkal<anoop.vijayan@in.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
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
# returned by Xen_EnabledLogicalElementCapabilities on giving invalid inputs.
#
# 1) Test by passing Invalid InstanceID Key Value
# Input:
# ------
# wbemcli gi http://localhost:5988/root/virt:\
# Xen_EnabledLogicalElementCapabilities.InstanceID="Wrong" -nl
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND
# error desc  : "The requested object could not be found"
#
# 2) Test by giving Invalid InstanceID Key Name
# Input:
# ------
# wbemcli gi http://localhost:5988/root/virt:\
# Xen_EnabledLogicalElementCapabilities.Wrong="Domain-0" -nl
#
# Output:
# -------
# error code  : CIM_ERR_FAILED
# error desc  : "No InstanceID specified"
#                                                   -Date 22.02.2008

import sys
import pywbem
from VirtLib import utils
from XenKvmLib import assoc
from XenKvmLib.common_util import try_getinstance
from XenKvmLib.vxml import XenXML, KVMXML, get_class
from XenKvmLib.classes import get_typed_class
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import log_param, logger, CIM_USER, CIM_PASS, CIM_NS, do_main

sup_types = ['Xen', 'KVM', 'XenFV']

expr_values = {
                "invalid_instid_keyname" :  {  'rc'   : pywbem.CIM_ERR_FAILED, \
                                               'desc' : "No InstanceID specified" }, \
                "invalid_instid_keyvalue" :  { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                               'desc' : "No such instance" }
              }

@do_main(sup_types)
def main():
    options = main.options
    log_param()
    status = PASS

    classname = get_typed_class(options.virt, 'EnabledLogicalElementCapabilities')

    conn = assoc.myWBEMConnection('http://%s' % options.ip, (CIM_USER, CIM_PASS), CIM_NS)

    # 1) Test by passing Invalid InstanceID Key Value
    field = 'INVALID_Instid_KeyValue'
    keys = { 'InstanceID' : field }
    ret_value = try_getinstance(conn, classname, keys, field_name=field, \
                                 expr_values=expr_values['invalid_instid_keyvalue'], bug_no="")
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid InstanceID Key Value.------")
        status = ret_value

    # 2) Test by giving Invalid InstanceID Key Name
    if options.virt == "Xen" or options.virt == "XenFV":
        inst_id = "Domain-0"
    else:
        test_dom = "qemu"
        vsxml = get_class(options.virt)(test_dom)
        ret = vsxml.define(options.ip)
        if not ret:
            logger.error("Failed to Define the dom: %s", test_dom)
            return FAIL    
        ret = vsxml.start(options.ip)
        if not ret:
            logger.error("Failed to Start the dom: %s", test_dom)
            return FAIL

        inst_id = test_dom

    field = 'INVALID_Instid_KeyName'
    keys = { field : inst_id }
    ret_value = try_getinstance(conn, classname, keys, field_name=field, \
                                expr_values=expr_values['invalid_instid_keyname'], bug_no="")
    if ret_value != PASS:
        logger.error("------ FAILED: Invalid InstanceID Key Name.------")
        status = ret_value
    if options.virt == "KVM":
        vsxml.destroy(options.ip)
        vsxml.undefine(options.ip)

    return status

if __name__ == "__main__":
    sys.exit(main())
