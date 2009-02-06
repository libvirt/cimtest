#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Veerendra Chandrappa <vechandr@in.ibm.com>
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

# For Ex: Command and the fields that are verified are given below. 
#
# wbemcli ain -ac Xen_VirtualSystemSettingDataComponent            
# 'http://localhost:5988/root/virt:Xen_VirtualSystemSettingData.InstanceID="Xen:
# domgst"'
#
# Output:
# localhost:5988/root/virt:Xen_ProcResourceAllocationSettingData.InstanceID=
# "domgst/0" 
#
# localhost:5988/root/virt:Xen_NetResourceAllocationSettingData.InstanceID=
# "domgst/00:22:33:aa:bb:cc" 
#
# localhost:5988/root/virt:Xen_DiskResourceAllocationSettingData.InstanceID=
# "domgst/xvda"
#
# localhost:5988/root/virt:Xen_MemResourceAllocationSettingData.InstanceID=
# "domgst/mem"
# 
# Using this output we call the SettingsDefineState association for each of them
#
# wbemcli ain -ac Xen_SettingsDefineState 'http://localhost:5988/root/virt:\
# Xen_ProcResourceAllocationSettingData.InstanceID="domgst/0"'
#
# Output:
# localhost:5988/root/virt:Xen_Processor.CreationClassName="Xen_Processor",\
# DeviceID="domgst/0",SystemCreationClassName="",SystemName="domgst"
#
#
# Date : 31-01-2008

import sys
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.const import do_main
from XenKvmLib.assoc import AssociatorNames, compare_all_prop
from XenKvmLib.vxml import get_class
from XenKvmLib.classes import get_typed_class
from XenKvmLib.rasd import enum_rasds
from XenKvmLib.devices import enum_dev
from XenKvmLib.common_util import parse_instance_id

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom    = "virtgst"

def setup_env(server, virt):
    if virt == 'Xen':
        test_disk = 'xvdb'
    else:
        test_disk = 'hdb'
    virt_xml = get_class(virt)
    if virt == 'LXC':
        cxml = virt_xml(test_dom)
    else:
        cxml = virt_xml(test_dom, disk = test_disk)

    ret = cxml.cim_define(server)
    if not ret:
        logger.error("Failed to Create the dom: %s", test_dom)
        return FAIL, cxml

    status = cxml.cim_start(server)
    if status != PASS:
        logger.error("Unable start dom '%s'", test_dom)
        cxml.undefine(server)
        return status, cxml

    return PASS, cxml

def init_rasd_list(virt, ip, guest_name):
    proc_rasd_cn = get_typed_class(virt, "ProcResourceAllocationSettingData")

    rasd_insts = {}

    rasds, status = enum_rasds(virt, ip)
    if status != PASS:
        logger.error("Enum RASDs failed")
        return rasd_insts, status

    for rasd_cn, rasd_list in rasds.iteritems():
        for rasd in rasd_list:
            guest, dev, status = parse_instance_id(rasd.InstanceID)
            if status != PASS:
                logger.error("Unable to parse InstanceID: %s", rasd.InstanceID)
                return rasd_insts, FAIL

            if guest == guest_name:
                rasd_insts[rasd.Classname] = rasd

    return rasd_insts, PASS

def init_device_list(virt, ip, guest_name):
    dev_insts = {}

    devs, status = enum_dev(virt, ip)
    if status != PASS:
        logger.error("Enum device instances failed")
        return dev_insts, status

    for dev_cn, dev_list in devs.iteritems():
        for dev in dev_list:
            guest, dev_id, status = parse_instance_id(dev.DeviceID)
            if status != PASS:
                logger.error("Unable to parse InstanceID: %s", dev.DeviceID)
                return dev_insts, FAIL

            if guest == guest_name:
                dev_insts[dev.Classname] = dev

    return dev_insts, PASS

def verify_rasd(virt, enum_list, rasds):
    if len(enum_list) != len(rasds):
        logger.error("Got %d RASDs, expected %d", len(enum_list), len(rasds))
        return FAIL

    status = FAIL

    for rasd in enum_list:
        exp_rasd = rasds[rasd.classname]

        if rasd['InstanceID'] != exp_rasd.InstanceID:
            logger.error("Got %s instead of %s", rasd['InstanceID'],
                         exp_rasd.InstanceID)
            return FAIL

        status = compare_all_prop(rasd, exp_rasd)
        if status != PASS:
            logger.error("Verifying instance properties failed.")

    return status 

def verify_devices(enum_list, devs):
    dev = enum_list[0]
    dev_cn = dev.classname

    if len(enum_list) != 1:
        logger.error("Got %d %s devices, expected 1", len(enum_list), dev_cn)
        return FAIL

    exp_dev = devs[dev_cn]

    if dev['DeviceID'] != exp_dev.DeviceID:
        logger.error("Got %s instead of %s", dev['DeviceID'], exp_dev.DeviceID)
        return FAIL

    status = compare_all_prop(dev, exp_dev)
    if status != PASS:
        return status

    return PASS

@do_main(sup_types)
def main():
    options = main.options
    virt = options.virt
    status = FAIL

    status, cxml = setup_env(options.ip, virt)
    if status != PASS:
        return status

    if virt == 'XenFV':
        VSType = 'Xen'
    else:
        VSType = virt 

    instIdval = "%s:%s" % (VSType, test_dom)

    try:
        rasds, status = init_rasd_list(virt, options.ip, test_dom)
        if status != PASS:
            raise Exception("Unable to build rasd instance list")

        vssdc_cn = get_typed_class(virt, 'VirtualSystemSettingDataComponent')
        vssd_cn = get_typed_class(virt, 'VirtualSystemSettingData')

        assoc = AssociatorNames(options.ip, vssdc_cn, vssd_cn,
                                InstanceID = instIdval)

        status = verify_rasd(virt, assoc, rasds)
        if status != PASS:
            raise Exception("Failed to verify RASDs")

        sds_cn = get_typed_class(virt, 'SettingsDefineState')

        devs, status = init_device_list(virt, options.ip, test_dom)
        if status != PASS:
            raise Exception("Unable to build device instance list")

        proc_cn = get_typed_class(virt, 'ProcResourceAllocationSettingData')
        for rasd in assoc:
            rasd_cn = rasd.classname
            
            # LXC guests don't have proc devices
            if virt == "LXC" and rasd_cn == proc_cn:
                continue

            sdc_assoc = AssociatorNames(options.ip, sds_cn, rasd_cn,
                                        InstanceID = rasd['InstanceID'])
            
            if len(sdc_assoc) < 1:
                raise Exception("%i dev insts for %s" % (len(sdc_assoc),
                                rasd['InstanceID']))

            status = verify_devices(sdc_assoc, devs)
            if status != PASS:
                raise Exception("Failed to verify devices")

    except Exception, details:
        logger.error(details)
        status = FAIL

    cxml.cim_destroy(options.ip)
    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())

