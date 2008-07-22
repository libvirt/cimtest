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

# This is a cross-provider testcase to 
# Knowing only the host name, determine which / how many virtual processors, 
# Memory, disk , network allocated
#
# It traverses the following path: 
# 
# {Hostsystem} --> [HostedResourcePool]--> [ElementAllocatedFromPool]
# and then Verify values of the Device instance returned
#
# Steps
# -----
# 1) Get the hostname by enumerating the hostsystem.
# 2) Create a diskconf file that is required for any queries w.r.t diskpool
# 3) Using the HostSystem info query the HostedResourcePool association.
# 4) Verify that 4 pools returned by HostedResourcePool.
# 5) Create a guest domain.
# 6) Create a pool list that was returned by HostedResourcePool.
# 7) Using the pool list created query the ElementAllocatedFromPool association.
# 8) Verify the various device instances returned.
# 9) Clear the diskpool conf file created initally.
# 10) Destory the domain.
#
#                                                             -Date: 12-02-2008


import sys
import os
from distutils.file_util import move_file
from VirtLib import utils
from CimTest.Globals import logger, CIM_ERROR_ASSOCIATORNAMES, \
CIM_ERROR_ASSOCIATORS
from CimTest.Globals import do_main
from XenKvmLib.assoc import AssociatorNames, Associators
from XenKvmLib.common_util import get_host_info
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from XenKvmLib.test_xml import testxml_bridge
from XenKvmLib.test_doms import test_domain_function, destroy_and_undefine_all
from VirtLib.live import network_by_bridge
from XenKvmLib.logicaldevices import verify_device_values
from XenKvmLib.common_util import cleanup_restore, test_dpath, \
create_diskpool_file

sup_types = ['Xen']

test_dom   = "CrossClass_GuestDom" 
test_mac   = "00:11:22:33:44:aa"
test_mem   = 128 
test_vcpus = 1 
test_disk  = "xvdb"
diskid = "%s/%s" % ("DiskPool", test_dpath)
memid = "%s/%s" % ("MemoryPool", 0)
procid = "%s/%s" % ("ProcessorPool", 0)

def setup_env(server):
    destroy_and_undefine_all(server)
    test_xml, bridge = testxml_bridge(test_dom, mem = test_mem, 
                                      vcpus = test_vcpus, mac = test_mac, 
                                      disk = test_disk, server = server)
    if bridge == None:
        logger.error("Unable to find virtual bridge")
        return SKIP

    if test_xml == None:
        logger.error("Guest xml was not created properly")
        return FAIL

    virt_network = network_by_bridge(bridge, server)
    if virt_network == None:
        logger.error("No virtual network found for bridge %s", bridge)
        return SKIP

    ret = test_domain_function(test_xml, server, cmd = "create")
    if not ret:
        logger.error("Failed to create the dom: %s", test_dom)
        return FAIL
    return PASS 

def print_err(err, detail, cn):
    logger.error(err % cn)
    logger.error("Exception: %s", detail)

def pool_init_list(pool_assoc):
    """
        Creating the lists that will be used for comparisons.
    """
    in_pllist = {}
    for i in range(len(pool_assoc)):
        classname_keyvalue = pool_assoc[i].classname
        instid =  pool_assoc[i]['InstanceID']
        in_pllist[classname_keyvalue] = instid
    return in_pllist

def eapf_list():
    disk  = {
              'SystemName'        : test_dom, 
              'CreationClassName' : "Xen_LogicalDisk", 
              'DeviceID'          : "%s/%s" % (test_dom,test_disk), 
              'Name'              : test_disk 
            }    
    proc = {
              'SystemName'        : test_dom, 
              'CreationClassName' : "Xen_Processor", 
              'DeviceID'          : "%s/%s" % (test_dom,0)
           }    
    net =  {
              'SystemName'        : test_dom, 
              'CreationClassName' : "Xen_NetworkPort", 
              'DeviceID'          : "%s/%s" % (test_dom, test_mac), 
              'NetworkAddresses'  : test_mac 
           }
    mem =  {
              'SystemName'        : test_dom, 
              'CreationClassName' : "Xen_Memory", 
              'DeviceID'          : "%s/%s" % (test_dom, "mem"), 
              'NumberOfBlocks'    : test_mem * 1024
           }
    eaf_values = {  "Xen_Processor"   : proc, 
                    "Xen_LogicalDisk" : disk, 
                    "Xen_NetworkPort" : net, 
                    "Xen_Memory"      : mem
                  }
    return eaf_values 

def get_inst_for_dom(assoc_val):
    dom_list = []

    for i in range(len(assoc_val)):
        if assoc_val[i]['SystemName'] == test_dom:
            dom_list.append(assoc_val[i])

    return dom_list

def get_assocname_info(server, cn, an, qcn, hostname):
    status = PASS
    assoc_info = []
    try:
        assoc_info = AssociatorNames(server,
                                         an,
                                         cn,
                       CreationClassName=cn,
                            Name = hostname)
        if len(assoc_info) < 1:
            logger.error("%s returned %i %s objects" % (an, 
                         len(assoc_info), qcn))
            status = FAIL

    except Exception, detail:
        print_err(CIM_ERROR_ASSOCIATORNAMES, detail, cn)
        status = FAIL

    if status != PASS:
        cleanup_restore(server, virt='Xen')
        test_domain_function(test_dom, server, "destroy")

    return status, assoc_info

def check_len(an, assoc_list_info, qcn, exp_len):
    if len(assoc_list_info) != exp_len:
        logger.error("%s returned %i %s objects" % (an, 
                     len(assoc_list_info), qcn))
        return FAIL
    return PASS

def verify_eafp_values(server, in_pllist):
    # Looping through the in_pllist to get association for various pools.
    status = PASS
    an = "Xen_ElementAllocatedFromPool"
    exp_len = 1
    qcn = "Logical Devices"
    eafp_values = eapf_list()
    for cn,  instid in sorted(in_pllist.items()):
        try:
            assoc_info = Associators(server, an, cn, InstanceID = instid)  
            inst_list = get_inst_for_dom(assoc_info)
            status = check_len(an, inst_list, qcn, exp_len)
            if status != PASS:
                break
            assoc_eafp_info = inst_list[0] 
            CCName = assoc_eafp_info['CreationClassName']
            status = verify_device_values(assoc_eafp_info, CCName, 
                                          eafp_values, virt='Xen')

            if status != PASS:
                return status

        except Exception, detail:
            logger.error(CIM_ERROR_ASSOCIATORS, an)
            logger.error("Exception: %s", detail)
            cleanup_restore(server, virt='Xen')
            status = FAIL
    return status

@do_main(sup_types)
def main():
    options= main.options
    server = options.ip
    virt=options.virt
    # Get the host info 
    status, host_name, classname = get_host_info(server)
    if status != PASS:
        return status

    # Verify DiskPool on machine
    status = create_diskpool_file() 
    if status != PASS:
        return status

    # Get the hostedResourcePool info first
    cn  = classname
    an  = "Xen_HostedResourcePool"
    qcn = "Device Pool"
    status, pool = get_assocname_info(server, cn, an, qcn, host_name)
    if status != PASS:
        return status

    # One pool for each Device type, hence len should be 4 
    exp_len = 4
    status = status = check_len(an, pool, qcn, exp_len)
    if status != PASS:
        return FAIL

    status = setup_env(server)
    if status != PASS:
        cleanup_restore(server, virt=virt)
        test_domain_function(test_dom, server, cmd = "destroy")
        return status

    in_pllist = pool_init_list(pool)
    status = verify_eafp_values(server, in_pllist)
    ret = test_domain_function(test_dom, server, cmd = "destroy")
    cleanup_restore(server, virt=virt)
    return status
if __name__ == "__main__":
    sys.exit(main())
