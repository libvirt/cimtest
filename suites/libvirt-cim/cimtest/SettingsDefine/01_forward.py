#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Kaitlin Rupert <karupert@us.ibm.com>
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

# This tc is used to verify the classname, InstanceID are  appropriately set for
# the Logical Devices of a domU when verified using the Xen_SettingsDefineState
# association.
# Date : 29-11-2007

import sys
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.vxml import get_class
from XenKvmLib.assoc import AssociatorNames
from XenKvmLib.classes import get_typed_class
from XenKvmLib.const import do_main, get_provider_version
from XenKvmLib.rasd import enum_rasds
from XenKvmLib.devices import enum_dev, dev_cn_to_rasd_cn 
from XenKvmLib.common_util import parse_instance_id

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
        logger.error("Failed to Create the dom: %s", test_dom)
        return FAIL, cmxl 

    status = cxml.cim_start(server, virt, test_dom)
    if status != PASS:
        logger.error("Unable start dom '%s'", test_dom)
        cxml.undefine(server)
        return status, cxml 

    return PASS, cxml 

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
                logger.error("Unable to parse InstanceID: %s" % dev.DeviceID)
                return dev_insts, FAIL

            if guest == guest_name:
                dev_insts[dev.Classname] = dev 

    return dev_insts, PASS

def init_rasd_list(virt, ip, guest_name):
    proc_rasd_cn = get_typed_class(virt, "ProcResourceAllocationSettingData")

    rasd_insts = {}

    rasds, status = enum_rasds(virt, ip)
    if status != PASS:
        logger.error("Enum RASDs failed")
        return rasd_insts, status

    for rasd_cn, rasd_list in rasds.iteritems():
        if virt == "LXC" and rasd_cn == proc_rasd_cn:
            continue

        for rasd in rasd_list:
            guest, dev, status = parse_instance_id(rasd.InstanceID)
            if status != PASS:
                logger.error("Unable to parse InstanceID: %s" % rasd.InstanceID)
                return rasd_insts, FAIL

            if guest == guest_name:
                rasd_insts[rasd.Classname] = rasd

    return rasd_insts, PASS

def verify_rasd(enum_list, rasds, rasd_cn, guest_name):
    for rasd in enum_list:
        guest, dev, status = parse_instance_id(rasd['InstanceID'])
        if status != PASS:
            logger.error("Unable to parse InstanceID: %s", rasd['InstanceID'])
            return status

        if guest != guest_name:
            continue

        exp_rasd = rasds[rasd_cn]

        print rasd['InstanceID'], exp_rasd.InstanceID
        if rasd['InstanceID'] == exp_rasd.InstanceID:
            status = PASS
        else:
            logger.info("Got %s instead of %s" % (rasd['InstanceID'],
                        exp_rasd.InstanceID))
            status = FAIL

    if status != PASS:
        logger.error("RASD with id %s not returned", exp_rasd.InstanceID)
        return FAIL

    return PASS

@do_main(sup_types)
def main():
    options = main.options
    status = FAIL 

    status, cxml = setup_env(options.ip, options.virt)
    if status != PASS:
        cxml.undefine(options.ip)
        return status

    try:
        devs, status = init_device_list(options.virt, options.ip, test_dom)
        if status != PASS:
            raise Exception("Unable to build device instance list")

        rasds, status = init_rasd_list(options.virt, options.ip, test_dom)
        if status != PASS:
            raise Exception("Unable to build rasd instance list")

        if len(devs) != len(rasds):
            raise Exception("%d device insts != %d RASD insts" % (len(devs),
                            len(rasds)))

        an = get_typed_class(options.virt, 'SettingsDefineState')
        for dev_cn, dev in devs.iteritems():
            ccn = dev.CreationClassName
            sccn = dev.SystemCreationClassName
            assoc_info = AssociatorNames(options.ip, an, ccn, 
                                         DeviceID = dev.DeviceID,
                                         CreationClassName = ccn,
                                         SystemName = dev.SystemName,
                                         SystemCreationClassName = sccn)

            if len(assoc_info) != 1:
                raise Exception("%i RASD insts for %s" % (len(assoc_info), 
                                dev.DeviceID))

            rasd_cn = dev_cn_to_rasd_cn(dev_cn, options.virt)
            status = verify_rasd(assoc_info, rasds, rasd_cn, test_dom)
            if status != PASS:
                raise Exception("Failed to verify RASDs")

    except Exception, details:
        logger.error(details)
        status = FAIL

    cxml.cim_destroy(options.ip)
    cxml.undefine(options.ip)
    return status
    
if __name__ == "__main__":
    sys.exit(main())

