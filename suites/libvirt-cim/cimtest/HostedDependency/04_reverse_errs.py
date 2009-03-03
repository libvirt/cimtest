#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
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

# This tc is used to verify Xen_HostedDependency asscoiation.
# returns exception when invalid values are passed.
# 
#  
# REVISIT : Update the expr_values with appropraite vaues once the 
# bug is fixed.
#                                                Date : 17-01-2008 

import sys
import pywbem 
from VirtLib import utils
from XenKvmLib import assoc
from XenKvmLib import vxml
from CimTest.Globals import logger, CIM_USER, CIM_PASS, CIM_NS
from XenKvmLib.const import do_main
from XenKvmLib.classes import get_typed_class
from XenKvmLib.common_util import get_host_info, try_assoc
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom = "hd_domain1"
test_mac = "00:11:22:33:44:55"

def set_expr_values(host_ccn):
    if (host_ccn == "Linux_ComputerSystem"):
        exp_rc =  pywbem.CIM_ERR_INVALID_PARAMETER
        exp_d1 = "INVALID"
        exp_d2 = "INVALID"
    else:
        exp_rc =  pywbem.CIM_ERR_NOT_FOUND
        exp_d1 = "No such instance (Name)"
        exp_d2 = "No such instance (CreationClassName)" 

    expr_values = {
                    "INVALID_KeyName"     : { 'rc' : exp_rc, 'desc' : exp_d1 },
                    "INVALID_NameValue"   : { 'rc' : exp_rc, 'desc' : exp_d1 },
                    "INVALID_CCNKeyName"  : { 'rc' : exp_rc, 'desc' : exp_d2 },
                    "INVALID_CCNameValue" : { 'rc' : exp_rc, 'desc' : exp_d2 }
                  }

    return expr_values 

def verify_err_fields(cxml, server, conn, keys, classname, 
                      assoc_classname, msg, field, expr_values):
    try:
        ret = try_assoc(conn, classname, assoc_classname, keys, 
                        field_name=field, expr_values=expr_values[field], 
                        bug_no="")
        if ret != PASS:
            logger.error("--- FAILED: %s---", msg)
            cxml.cim_destroy(server)
            cxml.cim_undefine(server)
    except Exception, details:
        logger.error("Exception: %s", details)
        cxml.cim_destroy(server)
        cxml.cim_undefine(server)
        return FAIL
    return ret

@do_main(sup_types)
def main():
    options = main.options
    server = options.ip 
    virt = options.virt

    virtxml = vxml.get_class(virt)
    if virt == "LXC":
        cxml = virtxml(test_dom)
    else:
        cxml = virtxml(test_dom, mac = test_mac)

    ret = cxml.cim_define(server)
    if not ret:
        logger.error("Failed to define the dom: %s", test_dom)
        return FAIL

    status = cxml.cim_start(server)
    if status != PASS:
        cxml.undefine(server)
        logger.error("Failed to start the dom: %s", test_dom)
        return FAIL

    conn = assoc.myWBEMConnection('http://%s' % server,
                                  (CIM_USER, CIM_PASS), CIM_NS)

    acn = get_typed_class(virt, 'HostedDependency')
    status, host_inst = get_host_info(server, virt)
    if status:
        logger.error("Unable to get host info")
        cxml.cim_destroy(server)
        cxml.undefine(server)
        return status

    classname = host_inst.CreationClassName 
    host_name = host_inst.Name

    expr_values = set_expr_values(classname)

    msg = 'Invalid Name Key Name'
    field = 'INVALID_KeyName'
    keys = { 'CreationClassName' : classname, field : host_name }
    ret_value = verify_err_fields(cxml, server, conn, keys, classname, 
                                  acn, msg, field, expr_values) 
    if ret_value != PASS: 
        return ret_value
      
    msg = 'Invalid Name Key Value'
    field='INVALID_NameValue'
    keys = { 'CreationClassName' : classname, 'Name'   : field }
    ret_value = verify_err_fields(cxml, server, conn, keys, classname, 
                                  acn, msg, field, expr_values) 
    if ret_value != PASS: 
        return ret_value

    msg = 'Invalid CreationClassName Key Name'
    field='INVALID_CCNKeyName'
    keys = {  field : classname, 'Name' : host_name }
    ret_value = verify_err_fields(cxml, server, conn, keys, classname, 
                                  acn, msg, field, expr_values)
    if ret_value != PASS: 
        return ret_value

    msg = 'Invalid CreationClassName Key Value'
    field='INVALID_CCNameValue'
    keys = { 'CreationClassName'  : field, 'Name'  : host_name }
    ret_value = verify_err_fields(cxml, server, conn, keys, classname, 
                                  acn, msg, field, expr_values)
    if ret_value == PASS:
        cxml.cim_destroy(server)
        cxml.undefine(server)
    return ret_value 
if __name__ == "__main__":
    sys.exit(main())


