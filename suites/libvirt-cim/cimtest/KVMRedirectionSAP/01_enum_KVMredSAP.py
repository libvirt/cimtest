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
# This test case is used to verify the KVMRedirectionSAP properties in detail.
# This test case verifies the following:
#
# When the domain is defined:
# KVMRedirectionSAP.Enabled = 3 and 
# KVMRedirectionSAP.[ElementName, Name] = port used in the GRASD:-1
#
# When the defined domain is started:
# KVMRedirectionSAP.Enabled = 6 and 
# KVMRedirectionSAP.[ElementName, Name] = port used in the GRASD:0
#
#                                               Date : 15-01-2009
#

import sys
from random import randrange
from XenKvmLib.vxml import get_class
from XenKvmLib.classes import get_typed_class
from XenKvmLib.const import do_main, get_provider_version
from XenKvmLib.enumclass import EnumInstances
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from XenKvmLib.const  import KVMRedSAP_proto, CIM_SAP_AVAILABLE_STATE,  \
                             CIM_SAP_INACTIVE_STATE

sup_types = ['Xen', 'KVM', 'LXC']
libvirtcim_redSAP_changes = 716
test_dom = 'test_kvmredsap_dom'

def enum_redsap(server, virt, classname):
    redsap_insts = { }
    status = FAIL

    try:
        redsap_list = EnumInstances(server, classname)
        for redsap in redsap_list:
            if redsap.SystemName == test_dom:
                if redsap.Classname not in redsap_insts.keys():
                    redsap_insts[redsap.Classname] = redsap
                    status = PASS
                else:
                    raise Exception("Got more than one record for: %s" \
                                     % test_dom)
    except Exception, details:
        logger.error(CIM_ERROR_ENUMERATE, classname)
        logger.error("Exception details: %s", details)

    return status, redsap_insts
         

def verify_redsap_values(val_list, redsap_inst, classname):
    try: 
        for key in val_list.keys():
            redsap = redsap_inst[classname]
            ret_val = eval('redsap.' + key)
            if ret_val != val_list[key]:
                raise Exception("'%s' Value Mismatch, Expected %s, Got %s" \
                                % (key, val_list[key], ret_val)) 
    except Exception, details:
        logger.error("Exception details: %s", details)
        return FAIL

    return PASS

@do_main(sup_types)
def main():
    virt = main.options.virt
    server = main.options.ip

    cname = 'KVMRedirectionSAP'
    classname = get_typed_class(virt, cname)

    # This check is required for libivirt-cim providers which do not have 
    # REDSAP changes in it and the REDSAP provider is available with 
    # revision >= 716.
    curr_cim_rev, changeset = get_provider_version(virt, server)
    if curr_cim_rev  < libvirtcim_redSAP_changes:
        logger.info("'%s' provider not supported, hence skipping the tc ....",
                    classname)
        return SKIP 

    vsxml = None
    action_start = False

    try:
        virt_xml =  get_class(virt)
        lport = randrange(5900, 5999)
        vsxml = virt_xml(test_dom, address='127.0.0.1', port_num=str(lport))

        # Define the VS, and verify the KVMRedirectionSAP values.
        ret = vsxml.cim_define(server)
        if not ret:
            raise Exception("Failed to define the dom: %s" % test_dom)

        # val_list that will be used for comparing with enum of 
        # KVMRedirectionSAP values
        sccn = get_typed_class(virt, 'ComputerSystem')
        val_list  = {
                       'SystemCreationClassName' : sccn, 
                       'SystemName'              : test_dom,
                       'CreationClassName'       : classname,
                       'KVMProtocol'             : KVMRedSAP_proto["vnc"],
                       'EnabledState'            : CIM_SAP_INACTIVE_STATE 
                    }
        val_list['ElementName'] = val_list['Name'] = "%s:-1" % lport 

        status, redsap_inst = enum_redsap(server, virt, classname)
        if status != PASS:
            raise Exception("Failed to get information on the defined dom:%s" \
                             % test_dom)

        status = verify_redsap_values(val_list, redsap_inst, classname)
        if status != PASS:
            raise Exception("Failed to verify information for the defined "\
                            "dom:%s" % test_dom)

        # For now verifying KVMRedirectoinSAP only for a defined LXC guest.
        # Once complete Graphics support for LXC is in, we need to verify the
        # KVMRedirectionSAP for a running guest.
        if virt == 'LXC':
            vsxml.undefine(server)
            return status

        # start the guest and verify the KVMRedirectionSAP values
        status = vsxml.cim_start(server)
        if not ret:
            raise Exception("Failed to start the dom: %s" % test_dom)

        status, redsap_inst = enum_redsap(server, virt, classname)
        if status != PASS:
            action_start = True         
            raise Exception("Failed to get information for running dom:%s" \
                             % test_dom)

        val_list['ElementName'] = val_list['Name'] = "%s:0" % lport
        val_list['EnabledState'] = CIM_SAP_AVAILABLE_STATE

        status = verify_redsap_values(val_list, redsap_inst, classname)
        if status != PASS:
            action_start = True         
            raise Exception("Failed to verify information for running dom:%s" \
                            % test_dom)

    except Exception, detail:
        logger.error("Exception: %s", detail)
        status = FAIL

    if action_start == True:
        vsxml.cim_destroy(server)

    vsxml.undefine(server)

    return status

if __name__ == "__main__":
    sys.exit(main())
