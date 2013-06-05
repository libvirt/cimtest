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
# This test case is used to verify the ResourceAllocationSettingData
# returns appropriate exceptions when invalid values are passed.
#
# 1) Test by giving invalid Invalid InstanceID Key Value
# Input:
# ------
# wbemcli gi 'http://localhost:5988/root/virt:Xen_MemResourceAllocationSetting\
# Data.InstanceID="Wrong"'
#
# Output:
# -------
# error code  : CIM_ERR_NOT_FOUND 
# error desc  : "No such instance"
#                                               

import sys
from pywbem import CIM_ERR_NOT_FOUND, CIMError
from pywbem.cim_obj import CIMInstanceName
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from XenKvmLib.vxml import get_class
from XenKvmLib.classes import get_typed_class
from XenKvmLib.const import default_network_name 
from XenKvmLib.enumclass import GetInstance, CIM_CimtestClass
from XenKvmLib.rasd import enum_rasds
from XenKvmLib.common_util import parse_instance_id

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom    = "VSSDC_dom"

def init_rasd_list(virt, ip, guest_name):
    rasd_insts = {}

    rasds, status = enum_rasds(virt, ip)
    if status != PASS:
        logger.error("Enum RASDs failed")
        return rasd_insts, status

    for rasd_cn, rasd_list in rasds.iteritems():
        for rasd in rasd_list:
            guest, dev, status = parse_instance_id(rasd.InstanceID)
            if status != PASS:
                logger.error("Unable to parse InstanceID: %s" % rasd.InstanceID)
                return rasd_insts, FAIL

            if guest == guest_name:
                rasd_insts[rasd.Classname] = rasd

    if len(rasds) != len(rasd_insts):
        logger.error("Expected %d RASDs, got %d", len(rasds), len(rasd_insts)) 
        return rasd_insts, FAIL

    return rasd_insts, PASS

@do_main(sup_types)
def main():
    options = main.options
    server = options.ip 
    virt = options.virt

    if virt == "Xen":
        test_disk = "xvda"
    else:
        test_disk = "hda"
    if options.virt == 'LXC':
        vsxml = get_class(virt)(test_dom)
    else:
        vsxml = get_class(virt)(test_dom, disk = test_disk)

    try:
        ret = vsxml.cim_define(options.ip)
        if not ret:
            logger.error("Failed to Define the domain: %s", test_dom)
            return FAIL 
    except Exception, details:
        logger.error("Exception : %s", details)
        return FAIL

    rasds, status = init_rasd_list(virt, options.ip, test_dom)
    if status != PASS:
        logger.error("Unable to build rasd instance list")
        return status

    expr_values = {
                   'rc'   : CIM_ERR_NOT_FOUND,
                   'desc' : 'No such instance' 
                  }

    keys = { 'InstanceID' : 'INVALID_Instid_KeyValue' }

    for cn, rasd_list in rasds.iteritems():
        status = FAIL

        ref = CIMInstanceName(cn, keybindings=keys)

        try:
            inst = CIM_CimtestClass(options.ip, ref)

        except CIMError, (err_no, err_desc):
            exp_rc    = expr_values['rc']
            exp_desc  = expr_values['desc']

            if err_no == exp_rc and err_desc.find(exp_desc) >= 0:
                logger.info("Got expected exception: %s %s", exp_desc, exp_rc)
                status = PASS
            else:
                logger.error("Unexpected errno %s, desc %s", err_no, err_desc)
                logger.error("Expected %s %s", exp_desc, exp_rc)

        if status != PASS:
            logger.error("------ FAILED: %s ------", cn)
            break

    vsxml.undefine(server)
    return status 

if __name__ == "__main__":
    sys.exit(main())
