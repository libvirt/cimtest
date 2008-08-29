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
from XenKvmLib import computersystem 
from XenKvmLib import assoc
from XenKvmLib.common_util import get_host_info
from XenKvmLib.classes import get_class_basename
from CimTest.Globals import logger, CIM_ERROR_ASSOCIATORS, \
CIM_ERROR_GETINSTANCE
from XenKvmLib.const import do_main
from XenKvmLib.devices import CIM_Instance
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV']

test_dom = "hd_domain1"
test_mac = "00:11:22:33:44:55"

def create_list(instance):
    new_list = {
                       'CreationClassName': instance.CreationClassName, \
                       'EnabledState'     : instance.EnabledState, \
                       'Name'             : instance.Name, \
                       'RequestedState'   : instance.RequestedState
               }
    return new_list

def print_error(field, ret_val, req_val):
    logger.error("%s Mismatch", field)
    logger.error("Returned %s instead of %s", ret_val, req_val)

def poll_for_enabledstate_value(server, virt): 
    status = PASS
    dom_field_list = {}
    check_reqstate_value = None
    timeout = 10
    try:
        for i in range(1, (timeout + 1)):
            sleep(1)
            cs = computersystem.get_cs_class(virt)
            dom_cs = cs(server, name=test_dom)
            if dom_cs.EnabledState == "" or dom_cs.CreationClassName == "" or \
               dom_cs.Name == "" or  dom_cs.RequestedState == "":
                logger.error("Empty EnabledState field.")
                status = FAIL
                return status, []

            dom_field_list = create_list(dom_cs) 
            check_reqstate_value = dom_field_list['EnabledState']
            if check_reqstate_value == 9:
                break

    except Exception, detail:
        logger.error(CIM_ERROR_GETINSTANCE, 'ComputerSystem')
        logger.error("Exception: %s" % detail)
        status = FAIL

    if check_reqstate_value != 9:
        logger.error("EnabledState has %i instead of 9.", check_reqstate_value)
        logger.error("Try to increase the timeout and run the test again")
        status = FAIL 
       
    return status, dom_field_list 

class HsError(Exception):
    pass

@do_main(sup_types)
def main():
    options = main.options

    status = PASS

    virtxml = vxml.get_class(options.virt)
    cxml = virtxml(test_dom, mac = test_mac)

    ret = cxml.create(options.ip)
    if not ret:
        logger.error("Failed to Create the dom: %s" % test_dom)
        status = FAIL
        return status

    ret = cxml.run_virsh_cmd(options.ip, "suspend")

    if not ret:
        logger.error("Failed to suspend the dom: %s" % test_dom)
        cxml.destroy(options.ip)
        cxml.undefine(options.ip)
        status = FAIL
        return status

    status, host_name, host_ccn = get_host_info(options.ip, options.virt)
    if status != PASS:
        logger.error("Failed to get host info")
        cxml.destroy(options.ip)
        cxml.undefine(options.ip)
        return status 

    try: 

#Polling for the value of EnabledState to be set to 9.
#We need to wait for the EnabledState to be set appropriately since
#it does not get set immediatley to value of 9 when suspended.

        dom_field_list = {}
        status, dom_field_list = poll_for_enabledstate_value(options.ip,
                                                             options.virt) 
        if status != PASS or len(dom_field_list) == 0:
            raise HsError("Failed to poll for enabled state value")

        hs = assoc.Associators(options.ip, "HostedDependency", 
                               get_class_basename(host_ccn), options.virt,
                               CreationClassName=host_ccn, Name=host_name)
        if len(hs) == 0:
            raise HsError("HostedDependency didn't return any instances.")

        hs_field_list = []
        for hsi in hs:
            if hsi['Name'] == test_dom:
                hs_field_list = create_list(CIM_Instance(hsi))

        if len(hs_field_list) == 0:
            raise HsError("Association did not return expected guest instance.")

        if dom_field_list['CreationClassName'] != hs_field_list['CreationClassName']:
            print_error('CreationClassName', hs_field_list['CreationClassName'], \
                                              dom_field_list['CreationClassName']) 
            status = FAIL
        if dom_field_list['Name'] != hs_field_list['Name']:
            print_error('Name', hs_field_list['Name'], \
                                 dom_field_list['Name']) 
            status = FAIL
            
        if dom_field_list['RequestedState'] != hs_field_list['RequestedState']:
            print_error('RequestedState', hs_field_list['RequestedState'], \
                                           dom_field_list['RequestedState']) 
            status = FAIL
        if dom_field_list['EnabledState'] != hs_field_list['EnabledState']:
            print_error('EnabledState', hs_field_list['EnabledState'], \
                                         dom_field_list['EnabledState']) 
            status = FAIL
    except HsError, detail:
        status = FAIL
        logger.error(detail)
    except Exception, detail:
        logger.error(CIM_ERROR_ASSOCIATORS,'HostedDependency')
        logger.error("Exception: %s" % detail)
        status = FAIL

    cxml.destroy(options.ip)
    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())


