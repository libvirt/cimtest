#!/usr/bin/env python

#
# Copyright 2011 IBM Corp.
#
# Authors:
#   Eduardo Lima (Etrunko) <eblima@br.ibm.com>
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

#
# Create a domain with cdrom device without media connected.
# ModifyResourceSettings call to change the cdrom media
#

import sys
import os
import pywbem

from CimTest.ReturnCodes import PASS, FAIL, XFAIL, SKIP
from CimTest.Globals import logger, CIM_USER, CIM_PASS, CIM_NS
from XenKvmLib.const import do_main, _image_dir, KVM_default_cdrom_dev
from XenKvmLib.classes import get_typed_class
from XenKvmLib.vxml import get_class
from XenKvmLib import vsms

supported = ['KVM',]

cim = None
sys_mgmt_service = None
domain = None

class CIMDomain(object):

    def __init__(self, name, virt, server):
        self.name = name
        self.server = server
        self.virt = virt
        self._domain = get_class(virt)(name)

        # CIM Instance for cdrom
        dasd = vsms.get_dasd_class(virt)
        cdrom_dasd = dasd(dev=KVM_default_cdrom_dev, source="",
                          name=name, emu_type=1)
        self._domain.res_settings.append(str(cdrom_dasd))

        # cdrom XML description
        devices = self._domain.get_node('/domain/devices')
        cdrom = self._domain.add_sub_node(devices, 'disk', type='file',
                                          device='cdrom')
        self._domain.add_sub_node(cdrom, 'source', file="")
        self._domain.add_sub_node(cdrom, 'target', dev=KVM_default_cdrom_dev)
    #__init__

    def define(self):
        return self._domain.cim_define(self.server)
    # define

    def undefine(self):
        return self._domain.undefine(self.server)
    # undefine

    def destroy(self):
        return self._domain.cim_destroy(self.server)
    #destroy
# CIMDomain


def set_device_addr(inst, address):
    return """
instance of %s {
    InstanceID="%s";
    ResourceType=%d;
    PoolID="%s";
    AllocationUnits="%s";
    Address="%s";
    VirtualQuantityUnits="%s";
    VirtualDevice="%s";
    EmulatedType=%d;
    BusType="%s";
    DriverName="%s";
    DriverType="%s";
};""" % (get_typed_class(domain.virt, "DiskResourceAllocationSettingData"),
        inst["InstanceID"],
        inst["ResourceType"],
        inst["PoolID"],
        inst["AllocationUnits"],
        address,
        inst["VirtualQuantityUnits"],
        inst["VirtualDevice"],
        inst["EmulatedType"],
        inst["BusType"],
        inst["DriverName"],
        inst["DriverType"],)
# set_device_addr()


def modify_media(cim, inst, addr):
    logger.info("Setting media addr to '%s'", addr)

    val = set_device_addr(inst, addr)
    ret = cim.InvokeMethod("ModifyResourceSettings", sys_mgmt_service, **{"ResourceSettings": [val,],})

    if ret[0]:
        logger.error("Modifying media: %s", ret)
        return None

    inst = cim.GetInstance(ret[1]["ResultingResourceSettings"][0])
    new_addr = inst["Address"]

    if new_addr != addr:
        logger.error("New media '%s' does not match expected '%s'", new_addr, addr)
        return None

    return inst
# modify_media()


@do_main(supported)
def main():
    options = main.options
    server = options.ip
    virt = options.virt

    server_url = "http://%s" % server
    global cim
    cim = pywbem.WBEMConnection(server_url, (CIM_USER, CIM_PASS), CIM_NS)

    _class = get_typed_class(virt, "VirtualSystemManagementService")
    global sys_mgmt_service
    sys_mgmt_service = cim.EnumerateInstanceNames(_class)[0]

    # Create new domain
    global domain
    domain = CIMDomain("cimtest_modify_cdrom", virt, server)
    if not domain.define():
        logger.error("Error defining test domain")
        return FAIL

    logger.info("Domain XML\n%s", domain._domain)
    # ein KVM_ComputerSystem
    _class = get_typed_class(virt, "ComputerSystem")
    computer_system_names = [i for i in cim.EnumerateInstanceNames(_class) if i["Name"] == domain.name]

    logger.info("ComputerSystem Names\n%s", computer_system_names)

    if not computer_system_names:
        logger.info("Host has no domains defined")
        return SKIP

    # ain -ac KVM_SystemDevice -arc KVM_LogicalDisk <KVM_ComputerSytem Name>
    a_class = get_typed_class(virt, "SystemDevice")
    r_class = get_typed_class(virt, "LogicalDisk")
    logical_disk_names = []

    for inst_name in computer_system_names:
        assoc_names = cim.AssociatorNames(inst_name, AssocClass=a_class, ResultClass=r_class)
        logical_disk_names.extend(assoc_names)

    logger.info("LogicalDisk Names\n%s", logical_disk_names)

    if not logical_disk_names:
        logger.info("No LogicalDisk instances returned")
        return FAIL

    # ai -arc KVM_DiskResourceAllocationSettingData <KVM_LogicalDisk Name>
    rclass = get_typed_class(virt, "DiskResourceAllocationSettingData")
    disk_rasd_names = []

    for inst_name in logical_disk_names:
        assoc_names = cim.AssociatorNames(inst_name, ResultClass=rclass)
        disk_rasd_names.extend(assoc_names)

    logger.info("DiskRASD names\n%s", disk_rasd_names)

    if not disk_rasd_names:
        logger.info("No DiskRASD instances returned")
        return FAIL

    cdrom_devices = [i for i in disk_rasd_names if cim.GetInstance(i)["EmulatedType"] == 1]

    logger.info("CDROM devices\n%s", cdrom_devices)

    if not cdrom_devices:
        logger.info("No CDROM device found")
        return FAIL

    cdrom = cdrom_devices[0]
    inst = cim.GetInstance(cdrom)

    for media in ["cdrom01.iso", "cdrom02.iso"]:
        if not inst:
            logger.error("Unable to get CDROM device instance")
            return FAIL

        # Get current media address
        old_media = inst["Address"]

        logger.info("Current CDROM media: '%s'", old_media)

        if not media and not old_media:
            logger.info("CDROM device has no media connected")
            continue

        # Need to eject first?
        if media and old_media:
            inst = modify_media(cim, inst, "")

        media_path = os.path.join(_image_dir, media)
        inst = modify_media(cim, inst, media_path)

    return PASS
# main()

if __name__ == "__main__":
    ret = main()

    if domain:
        domain.destroy()
        domain.undefine()

    sys.exit(ret)
