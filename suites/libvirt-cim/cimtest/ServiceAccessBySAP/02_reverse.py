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
from VirtLib import utils
from XenKvmLib.classes import get_typed_class
from CimTest import Globals
from XenKvmLib.const import do_main
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL, SKIP 
from XenKvmLib.const import get_provider_version
from XenKvmLib.enumclass import EnumInstances
from XenKvmLib.vxml import get_class
from XenKvmLib.assoc import AssociatorNames
from XenKvmLib.assoc import compare_all_prop

libvirtcim_servaccsap_changes = 784

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom = "domu1"

def setup_env(server, virt):
    if virt == 'Xen':
        test_disk = 'xvda'
    else:
        test_disk = 'hda'
    
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
                                    "for the same guest")
                kvmrsap_inst = kvmrsap
        
        if kvmrsap_inst is None:
            raise Exception("No kvmrsap instance found")

    except Exception, details:
        logger.error(details)
        return kvmrsap_inst, FAIL

    return kvmrsap_inst, PASS

def get_redirserv_inst(virt, ip):
    redirserv_inst = None

    try:
        redirserv_cn = get_typed_class(virt, 'ConsoleRedirectionService')

        enum_list = EnumInstances(ip, redirserv_cn)

        if len(enum_list) == 0:
            raise Exception("No ConsoleRedirectionService instance found")

        redirserv_inst = enum_list[0]

    except Exception, details:
        logger.error(details)
        return redirserv_inst, FAIL

    return redirserv_inst, PASS

def verify_redirserv(enum_list, redirserv_inst):
    status = PASS

    try:
        if len(enum_list) > 1:
            raise Exception("Association returned more than one redirection " +
                            "service instance")
        if len(enum_list) < 1:
            raise Exception("Association didn't return any redirection " +
                            "service instance")

        item = enum_list[0]

        if compare_all_prop(item, redirserv_inst) == FAIL:
            raise Exception("Redirection service returned by association is " +
                            "not equal redirection service instance returned " +
                            "by enumeration")
    except Exception, details:
        logger.error(details)
        status = FAIL
        
    return status

@do_main(sup_types)
def main():
    options = main.options
    server = options.ip
    virt = options.virt

    status = FAIL

    # This check is required for libvirt-cim providers which do not have 
    # ServiceAccessBySAP changes in it and the ServiceAccessBySAP 
    # association is available with revision >= 784.
    curr_cim_rev, changeset = get_provider_version(virt, server)
    if curr_cim_rev  < libvirtcim_servaccsap_changes:
        logger.info("'ServiceAccessBySAP' provider not supported, hence " +
                    "skipping the tc ....")
        return SKIP

    status, cxml = setup_env(options.ip, options.virt)
    if status != PASS:
        cxml.undefine(options.ip)
        return status


    try:
        redirserv_inst, status = get_redirserv_inst(options.virt,
                                                    options.ip) 
                                                    
        if status != PASS:
            raise Exception("Unable to get redirection service instance")
        
        kvmrsap_inst, status = get_kvmrsap_inst(options.virt, 
                                                options.ip, 
                                                test_dom)
        if status != PASS:
            raise Exception("Unable to get kvmrsap instance")
        
        an = get_typed_class(options.virt, 'ServiceAccessBySAP')

        sys_name = kvmrsap_inst.SystemName
        sys_ccn = kvmrsap_inst.SystemCreationClassName
        kvmrsap_ccn = kvmrsap_inst.CreationClassName
        kvmrsap_name = kvmrsap_inst.Name

        assoc_info = AssociatorNames(options.ip, an, kvmrsap_ccn,
                                     CreationClassName = kvmrsap_ccn,
                                     Name = kvmrsap_name,
                                     SystemCreationClassName = sys_ccn,
                                     SystemName = sys_name)

        status = verify_redirserv(assoc_info, redirserv_inst)

        if status != PASS:
            raise Exception("Failed to verify redirection service")

    except Exception, details:
        logger.error("Exception raised - ", details)
        status = FAIL

    cxml.cim_destroy(options.ip)
    cxml.undefine(options.ip)
    return status


if __name__ == "__main__":
        sys.exit(main())

