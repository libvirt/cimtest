#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Anoop V Chakkalakkal<anoop.vijayan@in.ibm.com>
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
# Testcase description
#
# Verify Xen_VirtualSystemSettingDataComponent reverse association returns error
# when invalid keyname/keyvalues are supplied
#
# 1. Verify Xen_VirtualSystemSettingDataComponent association returns error when
# invalid InstanceID keyname is supplied
#
# Input
# -----
# wbemcli ain -ac Xen_VirtualSystemSettingDataComponent \
# 'http://localhost:5988/root/virt: \
# Xen_VirtualSystemSettingData.wrong="Xen:virt1"' -nl
#
# Output
# ------
# rc   : CIM_ERR_NOT_FOUND
# desc : "No such instance (InstanceID)"
#
# 2. Verify Xen_VirtualSystemSettingDataComponent association returns error when
# invalid InstanceID keyvalue is supplied
#
# Input
# -----
# wbemcli ain -ac Xen_VirtualSystemSettingDataComponent \
# 'http://localhost:5988/root/virt: \
# Xen_VirtualSystemSettingData.InstanceID="wrong"' -nl
#
# Output
# ------
# rc   : CIM_ERR_NOT_FOUND
# desc : "No such instance (InstanceID)"
#
#                                                Date : 05-03-2008

import sys
import pywbem
from VirtLib import utils
from XenKvmLib import assoc
from XenKvmLib import vxml
from XenKvmLib.classes import get_typed_class
from XenKvmLib.common_util import try_assoc
from XenKvmLib.test_doms import destroy_and_undefine_all
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import do_main, logger
from CimTest.Globals import CIM_USER, CIM_PASS, CIM_NS

sup_types = ['Xen', 'XenFV', 'KVM']

test_dom     = "domu1"

expr_values = {
    "INVALID_InstID_Keyname"   : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                     'desc' : 'No such instance (InstanceID)' }, \
    "INVALID_InstID_Keyval"    : { 'rc'   : pywbem.CIM_ERR_NOT_FOUND, \
                     'desc' : 'No such instance (InstanceID)'}
}

def try_invalid_assoc(name_val, i, field, virt="Xen"):
    classname = get_typed_class(virt, 'VirtualSystemSettingData')
    ac_classname = get_typed_class(virt, 'VirtualSystemSettingDataComponent')
    keys = {}
    temp = name_val[i]
    name_val[i] = field
    for j in range(len(name_val)/2):
        k = j * 2
        keys[name_val[k]] = name_val[k+1]
    ret_val = try_assoc(conn, classname, ac_classname, keys, field_name=field, \
                              expr_values=expr_values[field], bug_no='')
    if ret_val != PASS:
        logger.error("------ FAILED: %s %s------", classname, field)
    name_val[i] = temp
    return ret_val


@do_main(sup_types)
def main():
    options = main.options
    if not options.ip:
        parser.print_help()
        return FAIL

    status = PASS

    destroy_and_undefine_all(options.ip)

    virt_xml = vxml.get_class(options.virt)
    cxml = virt_xml(test_dom)
    ret = cxml.create(options.ip)
    if not ret:
        logger.error('Unable to create domain %s' % test_dom)
        return FAIL

    global conn
    conn = assoc.myWBEMConnection('http://%s' % options.ip, (CIM_USER, \
                                                        CIM_PASS), CIM_NS)

    tc_scen = ['INVALID_InstID_Keyname', 'INVALID_InstID_Keyval']
  
    if options.virt == "Xen" or options.virt == "XenFV":
        inst_id = "Xen:%s" % test_dom
    else:
        inst_id = "KVM:%s" % test_dom
  
    name_val = ['InstanceID', inst_id]

    for i in range(len(tc_scen)):
        retval = try_invalid_assoc(name_val, i, tc_scen[i], options.virt)
        if retval != PASS:
            status = retval

    cxml.destroy(options.ip)
    cxml.undefine(options.ip)

    return status

if __name__ == "__main__":
    sys.exit(main())


