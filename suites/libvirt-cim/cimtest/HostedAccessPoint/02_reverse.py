#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
#
# Authors:
#    Richard Maciel <rmaciel@linux.vnet.ibm.com>
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

import sys
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from XenKvmLib.vxml import get_class
from XenKvmLib.assoc import AssociatorNames
from XenKvmLib.classes import get_typed_class
from XenKvmLib.const import do_main, get_provider_version
from XenKvmLib.common_util import get_host_info
from XenKvmLib.enumclass import EnumInstances
from XenKvmLib.assoc import compare_all_prop

libvirtcim_hostedAccPnt_changes = 782

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom = "domu1"

def setup_env(server, virt):
    if virt == 'Xen':
        test_disk = 'xvda'
    else:
        test_disk = 'vda'
    
    virt_xml = get_class(virt)
    if virt == 'LXC':
        cxml = virt_xml(test_dom)
    else:
        cxml = virt_xml(test_dom, disk = test_disk)

    ret = cxml.cim_define(server)
    if not ret:
        logger.error("Failed to define the dom: %s", test_dom)
        return FAIL, cxml

    status = cxml.cim_start(server)
    if status != PASS:
        logger.error("Unable start dom '%s'", test_dom)
        cxml.undefine(server)
        return status, cxml

    return PASS, cxml

def get_kvmrsap_inst(virt, ip, guest_name):
    kvmrsap_inst = None 

    try:
        kvmrsap_cn = get_typed_class(virt, 'KVMRedirectionSAP')
        enum_list = EnumInstances(ip, kvmrsap_cn)

        for kvmrsap in enum_list:
            if kvmrsap.SystemName == guest_name:
                if kvmrsap_inst is not None:
                    raise Exception("More than one KVMRedirectionSAP found " +
                                    "the same guest")
                kvmrsap_inst = kvmrsap

    except Exception, details:
        logger.error(details)
        return kvmrsap_inst, FAIL

    return kvmrsap_inst, PASS

def verify_host(enum_list, host_inst): 
    status = FAIL

    try:
        if len(enum_list) > 1:
            raise Exception("More than one host found!")
        if len(enum_list) < 1:
            raise Exception("No host found!")

        item = enum_list[0]
        status = compare_all_prop(item, host_inst)

    except Exception, details:
        logger.error(details)
        status = FAIL

    return status


@do_main(sup_types)
def main():
    options = main.options
    status = FAIL
    server = options.ip
    virt = options.virt

    # This check is required for libvirt-cim providers which do not have 
    # HostedAccessPoint changes in it and the HostedAccessPoint 
    # association is available with revision >= 782.
    curr_cim_rev, changeset = get_provider_version(virt, server)
    if curr_cim_rev  < libvirtcim_hostedAccPnt_changes:
        logger.info("'HostedAccessPoint' provider not supported, hence " +
                    "skipping the tc ....")
        return SKIP
        
    if options.virt == 'LXC':
        logger.info("VNC is not supported by LXC, hence skipping the tc ....")
        return SKIP

    status, cxml = setup_env(options.ip, options.virt)
    if status != PASS:
        cxml.undefine(options.ip)
        return status

    try:
        status, host_inst = get_host_info(server, virt)
        if status != PASS:
            raise Exception("Failed to get host info.")
        
        kvmrsap_inst, status = get_kvmrsap_inst(options.virt, 
                                                options.ip, 
                                                test_dom)
        if status != PASS:
            raise Exception("Unable to fetch kvmrsap instance (domain: %s)",
                            test_dom)
        if kvmrsap_inst is None:
            raise Exception("No kvmrsap instance returned")

        an = get_typed_class(options.virt, 'HostedAccessPoint')
            
        kvm_ccn = kvmrsap_inst.CreationClassName
        name = kvmrsap_inst.Name
        sys_ccn = kvmrsap_inst.SystemCreationClassName
        sys_name = kvmrsap_inst.SystemName

        assoc_info = AssociatorNames(options.ip, an, kvm_ccn, 
                                     CreationClassName = kvm_ccn,
                                     Name = kvmrsap_inst.Name,
                                     SystemCreationClassName = sys_ccn,
                                     SystemName = sys_name)

        status = verify_host(assoc_info, host_inst)

        if status != PASS:
            raise Exception("Failed to verify KVMRedirectionSAPs")

    except Exception, details:
        logger.error(details)
        status = FAIL

    cxml.cim_destroy(options.ip)
    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())
