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
# This tc is used to verify the classname, InstanceID and certian prop are 
# appropriately set for the domains when verified using the 
# Xen_ElementAllocatedFromPool asscoiation.
#
# Example command for LogicalDisk w.r.t to Xen_ElementAllocatedFromPool \
# asscoiation :
# wbemcli ai -ac Xen_ElementAllocatedFromPool \
# 'http://localhost:5988/root/virt:Xen_DiskPool.InstanceID="DiskPool/foo"'
# 
# Output:
# localhost:5988/root/virt:Xen_LogicalDisk.CreationClassName="Xen_LogicalDisk",\
# DeviceID="xen1/xvdb",SystemCreationClassName="",SystemName="xen1"
# ....
#-SystemName="xen1"
#-CreationClassName="Xen_LogicalDisk"
#-DeviceID="xen1/xvda  "
#-Primordial=FALSE
#-Name="xvda"
# .....
# 
# Similarly we check for Memory,Network,Processor.
#
#                                                Date : 29-11-2007

import sys
import os
import pywbem
from XenKvmLib.assoc import Associators
from XenKvmLib.vxml import get_class
from CimTest.Globals import logger, CIM_ERROR_ASSOCIATORS
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.test_doms import destroy_and_undefine_all
from XenKvmLib.classes import get_typed_class
from XenKvmLib.logicaldevices import verify_device_values
from XenKvmLib.const import default_pool_name

sup_types = ['Xen' , 'KVM', 'XenFV', 'LXC']

test_dom   = "eafp_domain"
test_mac   = "00:11:22:33:44:aa"
test_mem   = 128 
test_vcpus = 4 

def init_pllist(virt, vsxml, diskid):
    keys  = {
                'MemoryPool'    : 'MemoryPool/0',
            }
    if virt != 'LXC':
        virt_network = vsxml.xml_get_net_network()
        keys['DiskPool']      = 'DiskPool/%s' % default_pool_name 
        keys['ProcessorPool'] = 'ProcessorPool/0'
        keys['NetworkPool']   = 'NetworkPool/%s' %virt_network

    pllist = { }
    for cn, k in keys.iteritems():
        cn = get_typed_class(virt, cn)
        pllist[cn] =  k 

    return pllist

def eafp_list(virt, test_disk):
    mcn = get_typed_class(virt, "Memory")
    mem =  {
              'SystemName'        : test_dom,
              'CreationClassName' : mcn,
              'DeviceID'          : "%s/%s" % (test_dom, "mem"),
              'NumberOfBlocks'    : test_mem * 1024
           }

    eaf_values = { mcn :  mem }

    if virt != 'LXC':
        dcn = get_typed_class(virt, "LogicalDisk")
        pcn = get_typed_class(virt, "Processor")
        ncn = get_typed_class(virt, "NetworkPort")

        disk  = {
                  'SystemName'        : test_dom,
                  'CreationClassName' : dcn,
                  'DeviceID'          : "%s/%s" % (test_dom, test_disk),
                  'Name'              : test_disk
                }
        proc = {
                  'SystemName'        : test_dom,
                  'CreationClassName' : pcn, 
                  'DeviceID'          : None
               }
        net =  {
                  'SystemName'        : test_dom,
                  'CreationClassName' : ncn,
                  'DeviceID'          : "%s/%s" % (test_dom, test_mac),
                  'NetworkAddresses'  : test_mac
               }

        eaf_values[pcn] = proc
        eaf_values[dcn] = disk
        eaf_values[ncn] = net

    return eaf_values

def get_inst_for_dom(assoc_val):
     list = []

     for i in range(len(assoc_val)):
         if assoc_val[i]['SystemName'] == test_dom:
             list.append(assoc_val[i])

     return list


def verify_eafp_values(server, virt, in_pllist, test_disk):
    # Looping through the in_pllist to get association for various pools.
    eafp_values = eafp_list(virt, test_disk)
    an = get_typed_class(virt, "ElementAllocatedFromPool")
    for cn, instid in sorted(in_pllist.iteritems()):
        try:
            assoc_info = Associators(server, an, cn, InstanceID = instid)
            assoc_inst_list = get_inst_for_dom(assoc_info)
            if len(assoc_inst_list) < 1 :
                logger.error("'%s' with '%s' did not return any records for"
                             " domain: '%s'", an, cn, test_dom)
                return FAIL

            assoc_eafp_info = assoc_inst_list[0]
            CCName = assoc_eafp_info['CreationClassName']
            if  CCName == get_typed_class(virt, 'Processor'):
                if len(assoc_inst_list) != test_vcpus:
                    logger.error("'%s' should have returned '%i' Processor"
                                 " details, got '%i'", an, test_vcpus, 
                                 len(assoc_inst_list))
                    return FAIL
            
                for i in range(test_vcpus):
                    eafp_values[CCName]['DeviceID'] = "%s/%s" % (test_dom,i)
                    status = verify_device_values(assoc_inst_list[i], 
                                                  eafp_values, virt)
            else:
                status = verify_device_values(assoc_eafp_info, 
                                              eafp_values, virt)

            if status != PASS:
                return status 
        except Exception, detail:
            logger.error(CIM_ERROR_ASSOCIATORS, an)
            logger.error("Exception: %s", detail)
            status = FAIL
    return status

@do_main(sup_types)
def main():
    options = main.options

    loop = 0 
    server = options.ip
    virt = options.virt
    if virt == 'Xen':
        test_disk = 'xvdb'
    else:
        test_disk = 'hda'

    # Getting the VS list and deleting the test_dom if it already exists.
    destroy_and_undefine_all(server)
    virt_type = get_class(virt)
    if virt == 'LXC':
        vsxml = virt_type(test_dom, vcpus = test_vcpus)
    else:
        vsxml = virt_type(test_dom,  mem = test_mem, vcpus = test_vcpus, 
                          mac = test_mac, disk = test_disk)

    ret = vsxml.create(server)
    if not ret:
        logger.error("Failed to Create the dom: '%s'", test_dom)
        return FAIL

    # Get pool list against which the EAFP should be queried
    pllist = init_pllist(virt, vsxml, default_pool_name)

    
    status = verify_eafp_values(server, virt, pllist, test_disk)
    vsxml.destroy(server)
    return status

if __name__ == "__main__":
    sys.exit(main())
