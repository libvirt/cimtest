#!/usr/bin/python
################################################################################
# Copyright 2008 IBM Corp.
#
# Authors:
#    Veerendra C <vechandr@in.ibm.com>
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
################################################################################
# Example :
# wbemcli gi 'http://root:passwd@localhost:5988/root/virt:KVM_KVMRedirectionSAP.
# CreationClassName="KVM_KVMRedirectionSAP",Name="1:1",SystemCreationClassName=
# "KVM_ComputerSystem",SystemName="demo"' -nl
#
# Test Case Info:
# --------------
# This testcase is used to verify if appropriate exceptions are
# returned by KVMRedirectionSAP on giving invalid inputs for keyvalue's.
#
################################################################################

import sys
from pywbem import CIM_ERR_NOT_FOUND, CIMError, CIM_ERR_FAILED
from pywbem.cim_obj import CIMInstanceName
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from CimTest.Globals import logger
from XenKvmLib.classes import get_typed_class
from XenKvmLib import vxml
from XenKvmLib.const import do_main, get_provider_version
from XenKvmLib.enumclass import EnumInstances, CIM_CimtestClass

test_dom = "demo"
test_vcpus = 1
sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']

def get_sap_inst(virt, ip, cn, guest_name):
    try:
        enum_list = EnumInstances(ip, cn)

        if enum_list < 1:
            logger.error("No %s instances returned", cn)
            return None, FAIL

        for item in enum_list:
            if item.SystemName == guest_name:
                return item, PASS

    except Exception, details:
        logger.error(details)

    return None, FAIL

@do_main(sup_types)
def main():
    options = main.options
    libvirtcim_hr_crs_changes = 688
    status = FAIL

    # This check is required for libivirt-cim providers which do not have
    # CRS changes in it and the CRS provider is available with revision >= 688.
    curr_cim_rev, changeset = get_provider_version(options.virt, options.ip)
    if (curr_cim_rev < libvirtcim_hr_crs_changes):
        logger.info("ConsoleRedirectionService provider not supported, "
                   "hence skipping the test ....")
        return SKIP

    # Getting the VS list and deleting the test_dom if it already exists.
    cxml = vxml.get_class(options.virt)(test_dom, vcpus=test_vcpus)
    ret = cxml.cim_define(options.ip)

    if not ret :
        logger.error("ERROR: VS '%s' is not defined", test_dom)
        return status

    classname = get_typed_class(options.virt, 'KVMRedirectionSAP')

    sap, status = get_sap_inst(options.virt, options.ip, classname, test_dom)
    if status != PASS:
        cxml.undefine(options.ip)
        return status
    
    key_vals = { 
                'SystemName'             : sap.SystemName,
                'CreationClassName'      : sap.CreationClassName,
                'SystemCreationClassName': sap.SystemCreationClassName, 
                'Name'                   : sap.Name 
    }

    expr_values = {
        "invalid_ccname"   : {'rc'   : CIM_ERR_NOT_FOUND,
                     'desc' : "No such instance (CreationClassName)" },
        "invalid_sccname"  : {'rc'   : CIM_ERR_NOT_FOUND,
                     'desc' : "No such instance (SystemCreationClassName)" },
        "invalid_nameport" : {'rc'   : CIM_ERR_FAILED,
                     'desc' : "Unable to determine console port for guest" },
        "invalid_sysval"   : {'rc'   : CIM_ERR_NOT_FOUND,
                     'desc' : "No such instance" }
    }

    tc_scen = {
               'invalid_ccname'   : 'CreationClassName',
               'invalid_sccname'  : 'SystemCreationClassName',
               'invalid_nameport' : 'Name',
               'invalid_sysval'   : 'SystemName',
    } 

    # Looping by passing invalid key values 
    for test_val, field in tc_scen.items():
        newkey_vals = key_vals.copy()
        newkey_vals[field] = test_val 
        exp_values = expr_values[test_val]

        ref = CIMInstanceName(classname, keybindings=newkey_vals)

        try:
            inst = CIM_CimtestClass(options.ip, ref)

        except CIMError, (err_no, err_desc):
            exp_rc    = exp_values['rc']
            exp_desc  = exp_values['desc']

            if err_no == exp_rc and err_desc.find(exp_desc) >= 0:
                logger.info("Got expected exception: %s %s", exp_desc, exp_rc)
                status = PASS
            else:
                logger.error("Unexpected errno %s, desc %s", err_no, err_desc)
                logger.error("Expected %s %s", exp_desc, exp_rc)


        if status != PASS:
            logger.error(" -------------- FAILED %s ----------- : ", test_val)
            break

    cxml.cim_destroy(options.ip)
    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())

