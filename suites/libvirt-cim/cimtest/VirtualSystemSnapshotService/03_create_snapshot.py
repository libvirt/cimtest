#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
#
# Authors:
#    Kaitlin Rupert <karupert@us.ibm.com>
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
# Description:
#   This test verfies that calling CreateSnapshot() on a running guest
#   is successful and this it returns the proper Job and VSSD instances.
#

import sys
from pywbem import cim_types
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.const import do_main, get_provider_version
from XenKvmLib.vxml import get_class
from XenKvmLib.classes import get_typed_class, inst_to_mof
from XenKvmLib.enumclass import EnumNames, EnumInstances, GetInstance
from XenKvmLib.vsss import remove_snapshot 

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

#32769 - create a snapshot of the guest and leave the guest in a
#        'suspended' state
SNAPSHOT = cim_types.Uint16(32769)
test_dom = "snapshot_vm"

libvirt_cim_res_snap_rev = 876

def get_cs_ref(virt, ip):
    cs_cn = get_typed_class(virt, "ComputerSystem")

    cs_refs = EnumNames(ip, cs_cn)
    if cs_refs is None or len(cs_refs) < 1:
        logger.error("Exp at least one domain defined on the system")
        return FAIL, None

    cs_ref = None
    for ref in cs_refs:
        if ref['Name'] == test_dom:
            cs_ref = ref
            break

    if cs_ref is None:
        logger.error("Enum of %s didn't return %s", cs_cn, test_dom)
        return FAIL, None

    return PASS, cs_ref

def get_vsssc_inst(virt, ip):
    vsssc_cn = get_typed_class(virt, "VirtualSystemSnapshotServiceCapabilities")

    vsssc_insts = EnumInstances(ip, vsssc_cn, ret_cim_inst=True)
    if vsssc_insts is None or len(vsssc_insts) < 1:
        logger.error("Exp at least one %s", vsssc_cn)
        return FAIL, None

    vsssc = vsssc_insts[0]
    
    #Override the additional instance values.  We only care about the key
    #values (eventhough CreateSnapshot takes a instance)
    for p in vsssc.properties.values():
        if p.name == "SynchronousMethodsSupported" or \
           p.name == "AynchronousMethodsSupported" or \
           p.name == "SnapshotTypesSupported":
            p.value = None

    vsssc = inst_to_mof(vsssc)

    return PASS, vsssc

@do_main(sup_types)
def main():
    options = main.options

    cxml = get_class(options.virt)(test_dom)

    try:
        ret = cxml.cim_define(options.ip)
        if not ret:
            raise Exception("Unable to define %s", test_dom)

        status = cxml.cim_start(options.ip)
        if status != PASS:
            raise Exception("Failed to start the defined domain: %s" % test_dom)

        status, cs_ref = get_cs_ref(options.virt, options.ip)
        if status != PASS:
            raise Exception("Unable to get reference for %s" % test_dom)
         
        status, vsssc = get_vsssc_inst(options.virt, options.ip)
        if status != PASS:
            raise Exception("Unable to get VSSSC instance")

        vsss_cn = get_typed_class(options.virt, "VirtualSystemSnapshotService")
        vsss_refs = EnumNames(options.ip, vsss_cn)
        if vsss_refs is None or len(vsss_refs) < 1:
            raise Exception("Exp at least one %s" % vsss_cn)

        service = vsss_refs[0]
        keys = { 'Name' : service['Name'], 
                 'CreationClassName' : service['CreationClassName'],
                 'SystemCreationClassName' : service['SystemCreationClassName'],
                 'SystemName' : service['SystemName']
               }
        service = GetInstance(options.ip, vsss_cn, keys)

        output = service.CreateSnapshot(AffectedSystem=cs_ref,
                                        SnapshotSettings=vsssc,
                                        SnapshotType=SNAPSHOT)

        ret = output[0]
        if ret != 0:
            raise Exception("Snapshot of %s failed!" % test_dom)
       
        if output[1]['Job'] is None:
            raise Exception("CreateSnapshot failed to return a CIM job inst")

        rev, changeset = get_provider_version(options.virt, options.ip)
        if rev >= libvirt_cim_res_snap_rev and \
           output[1]['ResultingSnapshot'] is None:
            raise Exception("CreateSnapshot failed to return ResultingSnapshot")

    except Exception, detail:
        logger.error("Exception: %s", detail)
        status = FAIL

    cxml.cim_destroy(options.ip)
    cxml.undefine(options.ip)

    remove_snapshot(options.ip, test_dom)

    return status 

if __name__ == "__main__":
    sys.exit(main())
    
