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
# Test Case Info:
# --------------
# This tc is used to verify the Xen_ElementSettingData association with various RASD's.
# 1) Test by giving Invalid InstanceID Key Name
# Input:
# ------
# wbemcli ain -ac Xen_ElementSettingData 'http://localhost/root/virt:\
# Xen_ProcResourceAllocationSettingData.Wrong="Domain-0/0"'
# 
# Output:
# -------
# error code  : CIM_ERR_FAILED
# error desc  : "Missing InstanceID"
# 
# 2) Test by passing Invalid InstanceID Key Value
# Input:
# ------
# wbemcli ain -ac Xen_ElementSettingData 'http://localhost/root/virt:\
# Xen_ProcResourceAllocationSettingData.InstanceID="Wrong"'
# 
# 
# Output:
# -------
# error code  : CIM_ERR_FAILED
# error desc  : "Error getting associated RASD"
# 
# 
#                                                                Date : 20-02-2008 

import sys
import pywbem
from XenKvmLib.test_xml import testxml
from VirtLib import utils
from XenKvmLib import assoc
from XenKvmLib.test_doms import test_domain_function, destroy_and_undefine_all
from CimTest.Globals import log_param, logger, CIM_USER, CIM_PASS, CIM_NS, \
CIM_ERROR_ASSOCIATORS
from CimTest.Globals import do_main
from XenKvmLib.common_util import try_assoc
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen']

test_dom = "hd_domain1"
test_mac = "00:11:22:33:44:55"

expr_values = {
                "invalid_instid_keyvalue" : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                              'desc' : 'No such instance' }, \
                "invalid_instid_keyname"  : { 'rc'   : pywbem.CIM_ERR_FAILED, \
                                              'desc' : 'Missing InstanceID' }
              }

@do_main(sup_types)
def main():
    options = main.options

    log_param()
    status = PASS
    destroy_and_undefine_all(options.ip)
    test_xml = testxml(test_dom, mac = test_mac)
    ret = test_domain_function(test_xml, options.ip, cmd = "create")
    if not ret:
        logger.error("Failed to Create the dom: %s" % test_dom)
        status = FAIL
        return status
    try:
        instid = 'Xen:%s' %test_dom
        rasd_list = assoc.Associators(options.ip,
                                    "Xen_VirtualSystemSettingDataComponent",
                                    "Xen_VirtualSystemSettingData",
                                    InstanceID = instid)
    except Exception:
        logger.error(CIM_ERROR_ASSOCIATORS, 'Xen_VirtualSystemSettingDataComponent')
        test_domain_function(test_dom, options.ip, cmd = "destroy")
        return FAIL
    if len(rasd_list) < 1:
        logger.error("eturned %i objects, expected at least 1", len(rasd_list))
        test_domain_function(test_dom, options.ip, cmd = "destroy")
        return FAIL
    conn = assoc.myWBEMConnection('http://%s' % options.ip, 
                                  (CIM_USER, CIM_PASS), CIM_NS)
    assoc_classname = 'Xen_ElementSettingData'
    for rasd in rasd_list:
        classname = rasd.classname
        field = 'INVALID_InstID_KeyName'
        keys = { field :  rasd['InstanceID'] }
        ret_value = try_assoc(conn, classname, assoc_classname, keys, 
                              field_name=field, 
                              expr_values=expr_values['invalid_instid_keyname'],
                              bug_no="")
        if ret_value != PASS: 
            logger.error("------ FAILED: Invalid InstanceID Key Name.------")
            status = ret_value 
        field = 'INVALID_InstID_KeyValue'
        keys = { 'InstanceID' :  field }
        ret_value = try_assoc(conn, classname, assoc_classname, keys, 
                             field_name=field,
                             expr_values=expr_values['invalid_instid_keyvalue'],
                             bug_no="")
        if ret_value != PASS: 
            logger.error("------ FAILED: Invalid InstanceID Key Value.------")
            status = ret_value
        if status != PASS:
            break
    test_domain_function(test_dom, options.ip, cmd = "destroy")
    return status
if __name__ == "__main__":
    sys.exit(main())
