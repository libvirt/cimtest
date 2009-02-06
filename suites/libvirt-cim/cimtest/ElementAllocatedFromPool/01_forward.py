#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
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

# This tc is used to verify the classname, InstanceID are 
# appropriately set for a given of the domains when verified using the 
# Xen_ElementAllocatedFromPool asscoiation.
#
# Example command for LogicalDisk w.r.t to Xen_ElementAllocatedFromPool \
# asscoiation :
#
# wbemcli ain -ac Xen_ElementAllocatedFromPool 
# 'http://localhost:5988/root/virt:
# Xen_LogicalDisk.CreationClassName="Xen_LogicalDisk",\
# DeviceID="hd_domain/xvda",SystemCreationClassName="",SystemName="hd_domain"'
# 
# Output:
# localhost:5988/root/virt:Xen_DiskPool.InstanceID="DiskPool/foo"
# 
# Similarly we check for Memory,Network,Processor.
#
#                                                Date : 26-11-2007

import sys
import pywbem
from XenKvmLib.assoc import Associators
from XenKvmLib.test_doms import destroy_and_undefine_all 
from XenKvmLib import devices
from XenKvmLib.enumclass import GetInstance 
from CimTest.Globals import CIM_ERROR_ASSOCIATORS, CIM_ERROR_GETINSTANCE
from XenKvmLib.vxml import get_class
from XenKvmLib.classes import get_typed_class
from XenKvmLib.logicaldevices import field_err
from CimTest.Globals import logger
from XenKvmLib.const import do_main, default_pool_name
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom = "hd_domain"
test_mac = "00:11:22:33:44:aa"
test_vcpus = 1 

def get_inst(server, virt, cn, key_list):
    cn_name = get_typed_class(virt, cn)
    inst = None 
    try:
        inst = GetInstance(server, cn_name, key_list)

    except Exception, details:
        logger.error("Exception %s", details)
        return None 

    if inst is None:
        logger.error("Expected at least one %s instance", cn_name)
        return None 

    return inst 

def get_pool_details(server, virt, vsxml, diskid):
    gi_inst_list = {}
    inst = None
    if virt != 'LXC':
        virt_network = vsxml.xml_get_net_network()
        keys  = {
                    'DiskPool'      : 'DiskPool/%s' % diskid,
                    'ProcessorPool' : 'ProcessorPool/0' ,
                    'MemoryPool'    : 'MemoryPool/0',
                    'NetworkPool'   : 'NetworkPool/%s' %virt_network
                }
    else:
        keys  = {
                    'MemoryPool'    : 'MemoryPool/0',
                }

    for cn, k in keys.iteritems():
        key_list = {"InstanceID" : k}
        inst = get_inst(server, virt, cn, key_list)
        if inst is None:
            return FAIL, gi_inst_list 
        cn = get_typed_class(virt, cn)
        gi_inst_list[cn] = { 'InstanceID' : inst.InstanceID, 
                             'PoolID'     : inst.PoolID
                           }
    return PASS, gi_inst_list 

def verify_eafp_values(server, virt, in_pllist, gi_inst_list):
    # Looping through the in_pllist to get association for devices.
    an = get_typed_class(virt, "ElementAllocatedFromPool")
    sccn = get_typed_class(virt, "ComputerSystem")
    for cn,  devid in sorted(in_pllist.iteritems()):
        try:
            assoc_info = Associators(server, an, cn, 
                                     DeviceID = devid, 
                                     CreationClassName = cn, 
                                     SystemName = test_dom,
                                     SystemCreationClassName = sccn, 
                                     virt=virt)
            if len(assoc_info) != 1:
                logger.error("%s returned %i ResourcePool objects for "
                             "domain '%s'", an, len(assoc_info), 
                             test_dom)
                return FAIL
            assoc_eafp_info = assoc_info[0] 
            CCName = assoc_eafp_info.classname
            gi_inst = gi_inst_list[CCName]
            if assoc_eafp_info['InstanceID'] != gi_inst['InstanceID']:
                field_err(assoc_eafp_info, gi_inst, 'InstanceID')
                return FAIL

            if assoc_eafp_info['PoolID'] != gi_inst['PoolID']:
                field_err(assoc_eafp_info, gi_inst, 'PoolID')
                return FAIL

        except Exception, detail:
            logger.error(CIM_ERROR_ASSOCIATORS, an)
            logger.error("Exception: %s", detail)
            return FAIL
    return PASS


@do_main(sup_types)
def main():
    options = main.options
    server = options.ip
    virt = options.virt 
    if virt == 'Xen':
        test_disk = 'xvda'
    else:
        test_disk = 'hda'

    # Getting the VS list and deleting the test_dom if it already exists.
    destroy_and_undefine_all(server)
    virt_type = get_class(virt)
    if virt == 'LXC':
        vsxml = virt_type(test_dom)
    else:
        vsxml = virt_type(test_dom, vcpus = test_vcpus, mac = test_mac,
                       disk = test_disk)

    ret = vsxml.cim_define(server)
    if not ret:
        logger.error("Failed to define the dom: '%s'", test_dom)
        return FAIL

    status = vsxml.cim_start(server)
    if status != PASS:
        logger.error("Failed to start the dom: '%s'", test_dom)
        vsxml.undefine(server)
        return FAIL
    try: 
        mem_cn  = get_typed_class(virt, "Memory")
        ldlist = { mem_cn      : "%s/%s" % (test_dom, "mem") }

        if virt != 'LXC':
            disk_cn = get_typed_class(virt, "LogicalDisk") 
            net_cn  = get_typed_class(virt, "NetworkPort")
            proc_cn =  get_typed_class(virt, "Processor")
            ldlist[disk_cn] = "%s/%s" % (test_dom, test_disk)
            ldlist[net_cn]  = "%s/%s" % (test_dom, test_mac)
            ldlist[proc_cn] = "%s/%s" % (test_dom, "0")

        status, gi_inst_list = get_pool_details(server, virt, vsxml, 
                                                default_pool_name)
        if status != PASS:
            raise Exception("Failed to get pool details")
 
        status = verify_eafp_values(server, virt, ldlist, gi_inst_list)
    except Exception, details:
        logger.error("Exception details : %s", details) 

    vsxml.destroy(server)
    vsxml.undefine(server)

    return status
    
if __name__ == "__main__":
    sys.exit(main())
