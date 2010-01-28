#!/usr/bin/python
#
# Copyright 2010 IBM Corp.
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
# Purpose:
#   Verify providers support floppy devices 
#
# Steps:
#  1) Create a guest with a regular disk device and a floppy device
#  2) Build RASD parameters, making sure to specify floppy device 
#  3) Verify guest is defined properly
#

import sys
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS, SKIP
from XenKvmLib.classes import get_typed_class, inst_to_mof
from XenKvmLib.rasd import get_rasd_templates 
from XenKvmLib.const import do_main, get_provider_version, \
                            KVM_secondary_disk_path, default_pool_name
from XenKvmLib.vxml import get_class
from XenKvmLib.vsms import VIRT_DISK_TYPE_FLOPPY
from XenKvmLib.common_util import parse_instance_id
from XenKvmLib.enumclass import EnumInstances

sup_types = ['Xen', 'XenFV', 'KVM']
test_dom = 'rstest_floppy'

floppy_rev = 1023 

def get_rasd_list(ip, virt, addr):
    drasd_cn = get_typed_class(virt, "DiskResourceAllocationSettingData")
    pool_id = "DiskPool/%s" % default_pool_name

    rasds = get_rasd_templates(ip, virt, pool_id)
    if len(rasds) < 1:
        logger.info("No RASD templates returned for %s", pool_id)
        return [] 

    rasd_list = {} 

    for rasd in rasds:
        if rasd.classname != drasd_cn:
            continue

        if rasd['EmulatedType'] == VIRT_DISK_TYPE_FLOPPY and \
           "Default" in rasd['InstanceID']:

            rasd['Address'] = addr
            rasd_list[rasd.classname] = inst_to_mof(rasd)

    return rasd_list 

def verify_floppy_disk(ip, virt, addr, guest_name):
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
            raise Exception("%s instance for %s not found" % (drasd_cn, 
                            guest_name))

        if inst.EmulatedType != VIRT_DISK_TYPE_FLOPPY:
            raise Exception("Expected device to be of %d type" % \
                            (VIRT_DISK_TYPE_FLOPPY))

    except Exception, details:
        logger.error(details)
        return FAIL

    return PASS 

@do_main(sup_types)
def main():
    options = main.options

    status = FAIL

    curr_cim_rev, changeset = get_provider_version(options.virt, options.ip)
    if curr_cim_rev < floppy_rev:
        logger.error("Floppy support is available in rev >= %s", floppy_rev)
        return SKIP

    cxml = get_class(options.virt)(test_dom)

    addr = KVM_secondary_disk_path

    guest_defined = False

    try:
        rasd_list = get_rasd_list(options.ip, options.virt, addr)
        if len(rasd_list) < 1:
            raise Exception("Unable to get template RASDs for %s" % test_dom)

        cxml.set_res_settings(rasd_list)
        ret = cxml.cim_define(options.ip)
        if not ret:
            raise Exception("Unable to define %s" % test_dom)

        guest_defined = True 

        status = verify_floppy_disk(options.ip, options.virt, addr, test_dom)
        if status != PASS:
            raise Exception("Failed to verify disk path for %s" % test_dom)

    except Exception, details:
        logger.error(details)
        status = FAIL

    if guest_defined == True: 
        cxml.undefine(options.ip)

    return status 

if __name__ == "__main__":
    sys.exit(main())
    
