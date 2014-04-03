#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Veerendra Chandrappa <vechandr@in.ibm.com>
#    Zhengang Li <lizg@cn.ibm.com>
#    Deepti B. Kalakeri <deeptik@linux.vnet.ibm.com>
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
from sets import Set
from XenKvmLib import assoc
from XenKvmLib import vxml
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger
from XenKvmLib.const import do_main, get_provider_version
from XenKvmLib.xm_virt_util import virsh_version, virsh_version_cmp
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
input_graphics_pool_rev = 757
controller_rev = 1310

test_dom = "test_domain"
test_mac = "00:11:22:33:44:55"
test_cpu = 3 

@do_main(sup_types)
def main():
    options = main.options
    server  = options.ip
    virt = options.virt
    
    if virt == 'Xen':
        test_disk = 'xvdb'
    elif virt == 'LXC':
        test_disk = '/tmp'
    else:
        test_disk = 'vdb'

    status = PASS
    virt_xml = vxml.get_class(virt)
    if virt == 'LXC':
        cxml = virt_xml(test_dom, vcpus = test_cpu, mac = test_mac)
    else:
        cxml = virt_xml(test_dom, vcpus = test_cpu, mac = test_mac, 
                        disk = test_disk)

    ret = cxml.cim_define(server)
    if not ret:
        logger.error('Unable to define domain %s', test_dom)
        return FAIL

    status = cxml.cim_start(server)
    if status != PASS:
        cxml.undefine(server)
        logger.error('Unable to start domain %s', test_dom)
        return status

    sd_classname = get_typed_class(virt, 'SystemDevice')
    cs_classname = get_typed_class(virt, 'ComputerSystem')

    devs = assoc.AssociatorNames(server, sd_classname, cs_classname,
                                 Name=test_dom, CreationClassName=cs_classname)
    if devs == None:
        logger.error("'%s' association failed", sd_classname)
        cxml.cim_destroy(server)
        cxml.undefine(server)
        return FAIL

    if len(devs) == 0:
        logger.error("No devices returned")
        cxml.destroy(server)
        cxml.undefine(server)
        return FAIL

    mem_cn = get_typed_class(virt, "Memory")
    exp_pllist = { mem_cn  : ['%s/mem' % test_dom] }
    
    input_cn = get_typed_class(virt, "PointingDevice")
    if virt == 'LXC':
        point_device = "%s/%s" %(test_dom, "mouse:usb")
    elif virt == 'Xen':
        point_device = "%s/%s" %(test_dom, "mouse:xen")
    else:
        point_device = "%s/%s" %(test_dom, "mouse:ps2")
        keybd_device = "%s/%s" %(test_dom, "keyboard:ps2")
        libvirt_version = virsh_version(server, virt)

    # libvirt 1.2.2 adds a keyboard as an input option for KVM domains
    # so we need to handle that
    if virt == 'KVM' and virsh_version_cmp(libvirt_version, "1.2.2") >= 0:
        exp_pllist[input_cn] = [point_device, keybd_device]
    else:
        exp_pllist[input_cn] = [point_device]

    disk_cn =  get_typed_class(virt, "LogicalDisk")
    exp_pllist[disk_cn] = [ '%s/%s' % (test_dom, test_disk)]

    curr_cim_rev, changeset = get_provider_version(virt, server)
    if virt != 'LXC':
        net_cn = get_typed_class(virt, "NetworkPort")
        exp_pllist[net_cn]  = ['%s/%s' % (test_dom, test_mac)]
                
        proc_cn = get_typed_class(virt, "Processor")
        exp_pllist[proc_cn] = [] 
        for i in range(test_cpu):
            exp_pllist[proc_cn].append( '%s/%s' % (test_dom, i))

        if curr_cim_rev >= input_graphics_pool_rev:
            graphics_cn = get_typed_class(virt, "DisplayController")
            exp_pllist[graphics_cn] = ['%s/vnc' % test_dom]

    # Need a version check too
    if curr_cim_rev >= controller_rev and virt == 'KVM':
        controller_cn = get_typed_class(virt, "Controller")
        exp_pllist[controller_cn] = []
        exp_pllist[controller_cn].append('%s/controller:pci:0' % test_dom)
        exp_pllist[controller_cn].append('%s/controller:usb:0' % test_dom)
 
    try:
        res_pllist = {}
        for items in devs: 
            if items.classname in res_pllist.keys(): 
                res_pllist[items.classname].append(items['DeviceID']) 
            else: 
                res_pllist[items.classname] = [items['DeviceID']] 

        #Verifying we get all the expected device class info
        if Set(exp_pllist.keys()) != Set(res_pllist.keys()):
            logger.error("Device Class mismatch")
            raise Exception("Expected Device class list: %s \n \t  Got: %s"
                            % (sorted(exp_pllist.keys()), 
                               sorted(res_pllist.keys())))

        #Verifying that we get only the expected deviceid 
        #for every device class 
        for key in exp_pllist.keys():
            if Set(exp_pllist[key]) != Set(res_pllist[key]):
                logger.error("DeviceID mismatch")
                raise Exception("Expected DeviceID: %s \n \t  Got: %s"
                                 % (sorted(exp_pllist[key]), 
                                    sorted(res_pllist[key])))
    except Exception, details:
         logger.error("Exception %s", details)
         status = FAIL

    cxml.destroy(server)
    cxml.undefine(server)
    return status
        
if __name__ == "__main__":
    sys.exit(main())
