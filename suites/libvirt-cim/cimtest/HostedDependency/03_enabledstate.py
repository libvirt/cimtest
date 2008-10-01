#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Zhengang Li <lizg@cn.ibm.com>
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

# This tc is used to verify the EnabledState, system name and the classname 
# are appropriately set for each of the domains when verified using the 
# Xen_HostedDependency asscoiation.
# The testcase expects that the EnabledState property is set to 9 for the 
# Domain "hd_domain1" since it is suspended.
#  
#                                                Date : 31-10-2007

import sys
from time import sleep
from VirtLib import utils
from XenKvmLib import vxml
from XenKvmLib import enumclass 
from XenKvmLib import assoc
from XenKvmLib.classes import get_typed_class
from XenKvmLib.common_util import get_host_info, print_field_error, \
poll_for_state_change, call_request_state_change
from XenKvmLib.classes import get_class_basename
from CimTest.Globals import logger, CIM_ERROR_ASSOCIATORS, \
CIM_ERROR_GETINSTANCE
from XenKvmLib.const import do_main
from XenKvmLib.devices import CIM_Instance
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC

sup_types = ['Xen', 'KVM', 'XenFV']

TIME = "00000000000000.000000:000"
test_dom = "hd_domain1"
test_mac = "00:11:22:33:44:55"
bug_sblim = "00007"

def create_list(instance):
    new_list = {
                       'CreationClassName': instance.CreationClassName, 
                       'EnabledState'     : instance.EnabledState, 
                       'Name'             : instance.Name, 
                       'RequestedState'   : instance.RequestedState
               }
    return new_list


def poll_for_enabledstate_value(server, virt): 
    status = PASS
    dom_field_list = {}
    timeout = 10
    try:
        status, dom_cs = poll_for_state_change(server, virt, test_dom, 9,
                                               timeout)
        if status != PASS:
            logger.error("Attributes for dom '%s' is not set as expected.",
                          test_dom)
            return FAIL, []

        dom_field_list = create_list(dom_cs) 

    except Exception, detail:
        logger.error(CIM_ERROR_GETINSTANCE, 'ComputerSystem')
        logger.error("Exception: %s" % detail)
        status = FAIL

    return status, dom_field_list 

def verify_fields(hs_ret_values, exp_hs_values):
    try:
        field_names  = exp_hs_values.keys()
        for field in field_names:
            if hs_ret_values[field] != exp_hs_values[field]:
                print_field_error(field,  hs_ret_values[field], 
                                  exp_hs_values[field])
                return FAIL
    except Exception, details:
        logger.error("Exception: In fn verify_fields() %s", details)
        return FAIL

    return PASS


@do_main(sup_types)
def main():
    options = main.options
    virt = options.virt
    server = options.ip

    status = PASS

    virtxml = vxml.get_class(virt)
    cxml = virtxml(test_dom, mac = test_mac)

    ret = cxml.cim_define(server)
    if not ret:
        logger.error("Failed to define the dom: %s" % test_dom)
        return FAIL 

    rc = call_request_state_change(test_dom, server, 2, TIME, virt)
    if rc != 0:
        logger.error("Failed to start the dom: %s" % test_dom)
        cxml.undefine(server)
        return FAIL 

    rc = call_request_state_change(test_dom, server, 9, TIME, virt)
    if rc != 0:
        logger.error("Failed to suspend the dom: %s" % test_dom)
        cxml.destroy(server)
        cxml.undefine(server)
        return FAIL 

    status, host_name, host_ccn = get_host_info(server, virt)
    if status != PASS:
        logger.error("Failed to get host info")
        cxml.destroy(server)
        cxml.undefine(server)
        return status 

    try: 

        #Polling for the value of EnabledState to be set to 9.
        #We need to wait for the EnabledState to be set appropriately since
        #it does not get set immediatley to value of 9 when suspended.

        dom_field_list = {}
        status, dom_field_list = poll_for_enabledstate_value(server, virt) 
        if status != PASS or len(dom_field_list) == 0:
            logger.error("Failed to poll for enabled state value")
            cxml.destroy(server)
            cxml.undefine(server)
            return FAIL

        assoc_cn = get_typed_class(virt, "HostedDependency")

        hs = assoc.Associators(server, assoc_cn, host_ccn, 
                               CreationClassName=host_ccn, Name=host_name)
        if len(hs) == 0:
            logger.error("HostedDependency didn't return any instances.")
            cxml.destroy(server)
            cxml.undefine(server)
            return XFAIL_RC(bug_sblim)

        hs_field_list = []
        for hsi in hs:
            if hsi['Name'] == test_dom:
                hs_field_list = create_list(CIM_Instance(hsi))

        if len(hs_field_list) == 0:
            logger.error("Association did not return expected guest instance.")
            cxml.destroy(server)
            cxml.undefine(server)
            return FAIL

        status = verify_fields(hs_field_list, dom_field_list)

    except Exception, detail:
        logger.error(CIM_ERROR_ASSOCIATORS,'HostedDependency')
        logger.error("Exception: %s" % detail)
        status = FAIL

    cxml.destroy(server)
    cxml.undefine(server)
    return status

if __name__ == "__main__":
    sys.exit(main())


