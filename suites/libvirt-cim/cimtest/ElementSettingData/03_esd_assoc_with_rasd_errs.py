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
from VirtLib import utils
from XenKvmLib import vxml
from XenKvmLib import assoc
from CimTest.Globals import logger, CIM_USER, CIM_PASS, CIM_NS, \
CIM_ERROR_ASSOCIATORS
from XenKvmLib.const import do_main
from XenKvmLib.common_util import try_assoc
from XenKvmLib.classes import get_typed_class
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom = "hd_domain1"
test_mac = "00:11:22:33:44:55"

vssdc_cn = "VirtualSystemSettingDataComponent"
vssd_cn = "VirtualSystemSettingData"
esd_cn = "ElementSettingData"

expr_values = {
                "invalid_instid_keyvalue" : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                                              'desc' : 'No such instance' }, \
                "invalid_instid_keyname"  : { 'rc'   : pywbem.CIM_ERR_FAILED, \
                                              'desc' : 'Missing InstanceID' }
              }

@do_main(sup_types)
def main():
    options = main.options

    status = PASS
    virtxml = vxml.get_class(options.virt)
    if options.virt == 'LXC':
        cxml = virtxml(test_dom)
    else:
        cxml = virtxml(test_dom, mac = test_mac)
    ret = cxml.create(options.ip)
    if not ret:
        logger.error("Failed to Create the dom: %s", test_dom)
        status = FAIL
        return status
    if options.virt == "XenFV":
        options.virt = "Xen"
    try:
        an = get_typed_class(options.virt, vssdc_cn)
        cn = get_typed_class(options.virt, vssd_cn)
        instid = '%s:%s' % (options.virt, test_dom)
        rasd_list = assoc.Associators(options.ip, an, cn, InstanceID=instid)
    except Exception:
        logger.error(CIM_ERROR_ASSOCIATORS, an)
        cxml.destroy(options.ip)
        cxml.undefine(options.ip)
        return FAIL
    if len(rasd_list) < 1:
        logger.error("returned %i objects, expected at least 1", len(rasd_list))
        cxml.destroy(options.ip)
        cxml.undefine(options.ip)
        return FAIL
    conn = assoc.myWBEMConnection('http://%s' % options.ip, 
                                  (CIM_USER, CIM_PASS), CIM_NS)
    assoc_classname = get_typed_class(options.virt, esd_cn)
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
    cxml.destroy(options.ip)
    cxml.undefine(options.ip)
    return status
if __name__ == "__main__":
    sys.exit(main())
