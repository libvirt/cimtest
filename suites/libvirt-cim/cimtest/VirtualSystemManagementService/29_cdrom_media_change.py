#!/usr/bin/python
#
# Copyright 2010 IBM Corp.
#
# Authors:
#    Sharad Mishra <snmishra@us.ibm.com>
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
# Purpose:
#   Verify providers support disk images with long paths / names
#
# Steps:
#  1) Define and start a guest with cdrom drive. 
#  2) Modify cdrom drive to point to another source.
#  3) Verify guest is now pointing to new locations.
#

import sys
import os 
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS, SKIP
from XenKvmLib.classes import get_typed_class, inst_to_mof
from XenKvmLib.rasd import get_rasd_templates
from XenKvmLib.const import do_main, get_provider_version, \
                            KVM_disk_path, KVM_secondary_disk_path, \
                            default_pool_name
from XenKvmLib.vxml import get_class
from XenKvmLib import vxml
from XenKvmLib.common_util import parse_instance_id
from XenKvmLib.enumclass import EnumInstances
from XenKvmLib import vsms
from XenKvmLib import vsms_util
from XenKvmLib.vsms import VIRT_DISK_TYPE_CDROM

sup_types = ['KVM']
test_dom = 'cddom'
cdrom_rev = 1056

def get_rasd_list(ip, virt, addr):
    drasd_cn = get_typed_class(virt, "DiskResourceAllocationSettingData")
    instanceid = "DiskPool/%s" % default_pool_name

    rasds = get_rasd_templates(ip, virt, instanceid)
    if len(rasds) < 1:
        logger.info("No RASD templates returned for %s", pool_id)
        return []

    for rasd in rasds:
        if rasd.classname != drasd_cn:
            continue
        if rasd['EmulatedType'] == VIRT_DISK_TYPE_CDROM and \
           "Default" in rasd['InstanceID']:
            rasd['source'] = addr
            rasd['Address'] = addr
            break
    return rasd

def change_cdrom_media(ip, virt, rasd, addr):
    status = FAIL
    service = vsms.get_vsms_class(virt)(ip)
    cxml = vxml.get_class(virt)(test_dom)
    dasd = vsms.get_dasd_class(virt)(dev=rasd['VirtualDevice'],
                                     source=addr,
                                     instanceid="cddom/hdc",
                                     name=test_dom)

    status = vsms_util.mod_disk_res(ip, service, cxml, dasd, addr)
    return status

def verify_cdrom_update(ip, virt, addr, guest_name):
    inst = None

    try:
        drasd_cn = get_typed_class(virt, 'DiskResourceAllocationSettingData')
        enum_list = EnumInstances(ip, drasd_cn)

        if enum_list < 1:
            raise Exception("No %s instances returned" % drasd_cn)

        for rasd in enum_list:
            guest, dev, status = parse_instance_id(rasd.InstanceID)
            if status != PASS:
                raise Exception("Unable to parse InstanceID: %s" % \
                                rasd.InstanceID)

            if guest == guest_name:
                inst = rasd
                break

        if inst is None or inst.Address != addr:
            raise Exception("Expected Address to be of %s" % \
                            KVM_secondary_disk_path)

        if inst.EmulatedType != VIRT_DISK_TYPE_CDROM:
            raise Exception("Expected device to be of %d type" % \
                            VIRT_DISK_TYPE_FLOPPY)

    except Exception, details:
        logger.error(details)
        return FAIL

    return PASS

@do_main(sup_types)
def main():
    options = main.options

    status = FAIL

    curr_cim_rev, changeset = get_provider_version(options.virt, options.ip)
    if curr_cim_rev < cdrom_rev:
        logger.error("cdrom media change support is available in rev >= %s", cdrom_rev)
        return SKIP

    cxml = get_class(options.virt)(test_dom)

    addr = KVM_disk_path

    guest_defined = False
    guest_running = False

    try:
        rasd = get_rasd_list(options.ip, options.virt, addr)
        rasd_list = {}
        rasd_list[rasd.classname] = inst_to_mof(rasd)
        if len(rasd_list) < 1:
            raise Exception("Unable to get template RASDs for %s" % test_dom)

        cxml.set_res_settings(rasd_list)
        ret = cxml.cim_define(options.ip)
        if not ret:
            raise Exception("Unable to define %s" % test_dom)

        guest_defined = True

        ret = cxml.cim_start(options.ip)
        if ret:
            raise Exception("Unable to start %s" % test_dom)

        guest_running = True

        status = change_cdrom_media(options.ip, options.virt, rasd, KVM_secondary_disk_path)
        if status != PASS:
            raise Exception("Failed cdrom media change for %s" % test_dom)

        status = verify_cdrom_update(options.ip, options.virt, KVM_secondary_disk_path, test_dom)
        if status != PASS:
            raise Exception("Failed to verify cdrom media change for %s" % test_dom)

    except Exception, details:
        logger.error(details)
        status = FAIL

    if guest_running == True:
        cxml.destroy(options.ip)

    if guest_defined == True:
        cxml.undefine(options.ip)

    return status

if __name__ == "__main__":
    sys.exit(main())


