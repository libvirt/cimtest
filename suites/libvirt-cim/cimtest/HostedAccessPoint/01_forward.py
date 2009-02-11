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

def list_kvmrsap_inst(virt, ip):
    list_kvmrsap = None

    try:
        kvmrsap_cn = get_typed_class(virt, 'KVMRedirectionSAP')
        list_kvmrsap = EnumInstances(ip, kvmrsap_cn)

    except Exception, details:
        logger.error(details)
        return list_kvmrsap, FAIL

    return list_kvmrsap, PASS

def verify_kvmrsap(enum_list, list_kvmrsap):

    if len(enum_list) == 0:
        return FAIL

    for item in enum_list:
        found = FAIL
        for kvmrsap in list_kvmrsap:
            found = compare_all_prop(item, kvmrsap)
            if found == PASS:
                break

        if found == FAIL:
            logger.error("Instance found in kvmrsap list but not in " +
                         "association list")
            return FAIL

    return PASS

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


    status, cxml = setup_env(options.ip, options.virt)
    if status != PASS:
        cxml.undefine(options.ip)
        return status

    try:
        status, host_inst = get_host_info(server, virt)
        if status != PASS:
            raise Exception("Failed to get host info.")

        list_kvmrsap, status = list_kvmrsap_inst(options.virt,
                                                 options.ip)
        if status != PASS:
            raise Exception("Unable to fetch kvmrsap instance")

        if list_kvmrsap is None or len(list_kvmrsap) == 0:
            raise Exception("No kvmrsap instance returned")

        an = get_typed_class(options.virt, 'HostedAccessPoint')

        host_ccn = host_inst.CreationClassName

        assoc_info = AssociatorNames(options.ip, an, host_ccn,
                                     CreationClassName = host_ccn,
                                     Name = host_inst.Name)

        status = verify_kvmrsap(assoc_info, list_kvmrsap)

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
