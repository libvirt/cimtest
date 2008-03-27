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
from XenKvmLib.test_xml import testxml, testxml_bridge
from VirtLib import utils
from XenKvmLib import assoc
from XenKvmLib.test_doms import test_domain_function, destroy_and_undefine_all 
from XenKvmLib import devices
from CimTest import Globals
from CimTest.Globals import do_main
from VirtLib.live import network_by_bridge
from CimTest.ReturnCodes import PASS, FAIL, SKIP

sup_types = ['Xen']

test_dom = "hd_domain"
test_mac = "00:11:22:33:44:aa"
test_vcpus = 1 
test_disk = 'xvda'


def print_error(cn, detail):
    Globals.logger.error(Globals.CIM_ERROR_GETINSTANCE, cn)
    Globals.logger.error("Exception: %s", detail)

def get_keys(cn, device_id):
    id = "%s/%s" % (test_dom, device_id)

    key_list = { 'DeviceID' : id,
                 'CreationClassName' : cn,
                 'SystemName' : test_dom,
                 'SystemCreationClassName' : "Xen_ComputerSystem"
               }

    return key_list

@do_main(sup_types)
def main():
    options = main.options
    status = PASS
    idx = 0

# Getting the VS list and deleting the test_dom if it already exists.
    destroy_and_undefine_all(options.ip)
    Globals.log_param()

    test_xml, bridge = testxml_bridge(test_dom, vcpus = test_vcpus, \
                                      mac = test_mac, disk = test_disk, \
                                      server = options.ip)
    if bridge == None:
        Globals.logger.error("Unable to find virtual bridge")
        return SKIP 

    if test_xml == None:
        Globals.logger.error("Guest xml not created properly")
        return FAIL 

    virt_network = network_by_bridge(bridge, options.ip)
    if virt_network == None:
        Globals.logger.error("No virtual network found for bridge %s", bridge)
        return SKIP 

    ret = test_domain_function(test_xml, options.ip, cmd = "create")
    if not ret:
        Globals.logger.error("Failed to Create the dom: %s", test_dom)
        return FAIL

    try: 
        cn = "Xen_LogicalDisk"
        key_list = get_keys(cn, test_disk)
        disk = devices.Xen_LogicalDisk(options.ip, key_list)
    except Exception,detail:
        print_error(cn, detail)
        return FAIL

    try: 
        cn = "Xen_Memory"
        key_list = get_keys(cn, "mem")
        mem = devices.Xen_Memory(options.ip, key_list)
    except Exception,detail:
        print_error(cn, detail)
        return FAIL

    try:
        cn = "Xen_NetworkPort"
        key_list = get_keys(cn, test_mac)
        net = devices.Xen_NetworkPort(options.ip, key_list)
    except Exception,detail:
        print_error(cn, detail)
        return FAIL

    try: 
        cn = "Xen_Processor"
        key_list = get_keys(cn, "0")
        proc = devices.Xen_Processor(options.ip, key_list)
    except Exception,detail:
        print_error(cn, detail)
        return FAIL

    netpool_id = "NetworkPool/%s" % virt_network

    lelist = {
              "Xen_LogicalDisk" : disk.DeviceID, \
              "Xen_Memory"      : mem.DeviceID, \
              "Xen_NetworkPort" : net.DeviceID, \
              "Xen_Processor"   : proc.DeviceID 
             }
    poollist = [  
              "Xen_DiskPool", \
              "Xen_MemoryPool", \
              "Xen_NetworkPool", \
              "Xen_ProcessorPool"
             ]
    poolval = [ 
               "DiskPool/foo", \
               "MemoryPool/0", \
               netpool_id, \
               "ProcessorPool/0"
             ]

    sccn = "Xen_ComputerSystem"
    for cn, devid in sorted(lelist.items()):
        try:
            assoc_info = assoc.Associators(options.ip, \
                                           "Xen_ElementAllocatedFromPool",
                                           cn,
                                           DeviceID = devid,
                                           CreationClassName = cn,
                                           SystemName = test_dom,
                                           SystemCreationClassName = sccn)
            if len(assoc_info) != 1:
                Globals.logger.error("Xen_ElementAllocatedFromPool returned %i\
 ResourcePool objects for domain '%s'", len(assoc_info), test_dom)
                status = FAIL
                break

            if assoc_info[0].classname != poollist[idx]:
                Globals.logger.error("Classname Mismatch")
                Globals.logger.error("Returned %s instead of %s", \
                                      assoc_info[0].classname, \
                                       poollist[idx])
                status = FAIL
                
            if assoc_info[0]['InstanceID'] !=  poolval[idx]: 
                Globals.logger.error("InstanceID Mismatch")
                Globals.logger.error("Returned %s instead of %s", \
                                      assoc_info[0]['InstanceID'], \
                                      poolval[idx])
                status = FAIL

            if status != PASS:
                break
            else:
               idx = idx + 1

        except Exception, detail:
            Globals.logger.error(Globals.CIM_ERROR_ASSOCIATORS, \
                                  'Xen_ElementAllocatedFromPool')
            Globals.logger.error("Exception: %s", detail)
            status = FAIL

    ret = test_domain_function(test_dom, options.ip, \
                                                   cmd = "destroy")
    return status
    
if __name__ == "__main__":
    sys.exit(main())
