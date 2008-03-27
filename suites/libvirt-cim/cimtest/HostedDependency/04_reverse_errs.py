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
from XenKvmLib.test_xml import testxml
from VirtLib import utils
from XenKvmLib import assoc
from XenKvmLib.test_doms import test_domain_function, destroy_and_undefine_all
from CimTest.Globals import log_param, logger, CIM_USER, CIM_PASS, CIM_NS
from CimTest.Globals import do_main
from XenKvmLib.common_util import get_host_info, try_assoc
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC

sup_types = ['Xen']

test_dom = "hd_domain1"
test_mac = "00:11:22:33:44:55"
bug='90264'

exp_rc = 6 #CIM_ERR_NOT_FOUND
exp_d1 = "No such instance (Name)"
exp_d2 = "No such instance (CreationClassName)" 

expr_values = {
                "invalid_name_keyname"    : { 'rc' : exp_rc, 'desc' : exp_d1 },
                "invalid_name_keyvalue"   : { 'rc' : exp_rc, 'desc' : exp_d1 },
                "invalid_ccname_keyname"  : { 'rc' : exp_rc, 'desc' : exp_d2 },
                "invalid_ccname_keyvalue" : { 'rc' : exp_rc, 'desc' : exp_d2 }
              }

def err_invalid_name_keyname(server, conn, field):
    status, host_name, classname = get_host_info(server)
    if status:
        return status
    assoc_classname = 'Xen_HostedDependency'
    keys = { 
              'CreationClassName' : classname, \
                            field : host_name 
           }
    return try_assoc(conn, classname, assoc_classname, keys, field_name=field, \
                              expr_values=expr_values['invalid_name_keyname'], \
                                                                     bug_no=bug)

def err_invalid_name_keyvalue(server, conn, field):
    status, host_name, classname = get_host_info(server)
    if status:
        return status
    assoc_classname = 'Xen_HostedDependency'
    keys = { 
              'CreationClassName' : classname, \
                         'Name'   : field
           }
    return try_assoc(conn, classname, assoc_classname, keys, field_name=field, \
                             expr_values=expr_values['invalid_name_keyvalue'], \
                                                                     bug_no=bug)

def err_invalid_ccname_keyname(server, conn, field):
    status, host_name, classname = get_host_info(server)
    if status:
        return status
    assoc_classname = 'Xen_HostedDependency'
    keys = {  
                field : classname, \
               'Name' : host_name
            }
    return try_assoc(conn, classname, assoc_classname, keys, field_name=field, \
                             expr_values=expr_values['invalid_ccname_keyname'], \
                                                                     bug_no=bug)
def err_invalid_ccname_keyvalue(server, conn, field):
    status, host_name, classname = get_host_info(server)
    if status:
        return status
    assoc_classname = 'Xen_HostedDependency'
    keys = {  
               'CreationClassName'  : field, \
               'Name'               : host_name
            }
    return try_assoc(conn, classname, assoc_classname, keys, field_name=field, \
                           expr_values=expr_values['invalid_ccname_keyvalue'], \
                                                                     bug_no=bug)

@do_main(sup_types)
def main():
    options = main.options

    log_param()
    status = PASS
    server = options.ip
    destroy_and_undefine_all(options.ip)
    test_xml = testxml(test_dom, mac = test_mac)

    ret = test_domain_function(test_xml, options.ip, cmd = "create")
    if not ret:
        logger.error("Failed to Create the dom: %s" % test_dom)
        status = FAIL
        return status
    conn = assoc.myWBEMConnection('http://%s' % options.ip, (CIM_USER, CIM_PASS), CIM_NS)
    ret_value = err_invalid_name_keyname(server, conn, field='INVALID_KeyName') 
    if ret_value != PASS: 
         logger.error("------ FAILED: Invalid Name Key Name.------")
         status = ret_value 
    ret_value = err_invalid_name_keyvalue(server, conn, field='INVALID_NameValue') 
    if ret_value != PASS: 
         logger.error("------ FAILED: Invalid Name Key Value.------")
         status = ret_value
    ret_value = err_invalid_ccname_keyname(server, conn, field='INVALID_CCNKeyName')
    if ret_value != PASS: 
         logger.error("------ FAILED: Invalid CreationClassName Key Name------")
         status = ret_value 
    ret_value = err_invalid_ccname_keyvalue(server, conn, field='INVALID_CCNameValue')
    if ret_value != PASS:
         logger.error("------ FAILED: Invalid CreationClassName Key Value------")
         status = ret_value
    ret = test_domain_function(test_dom, options.ip, cmd = "destroy")
    return status
if __name__ == "__main__":
    sys.exit(main())


