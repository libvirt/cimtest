#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
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
#   Verify providers support disk images with long paths / names
#
# Steps:
#  1) Create a disk image with a long path
#  2) Build RASD parameters, making sure to specify disk image created in step 1
#  3) Verify guest is defined properly
#

import sys
import os 
from VirtLib.utils import run_remote
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS
from XenKvmLib.classes import get_typed_class, inst_to_mof
from XenKvmLib.rasd import get_default_rasds
from XenKvmLib.const import do_main, _image_dir, get_provider_version
from XenKvmLib.vxml import get_class
from XenKvmLib.common_util import parse_instance_id
from XenKvmLib.enumclass import EnumInstances

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']
test_dom = 'rstest_disk_domain'
libvirt_cim_dasd_caption = 707

def make_long_disk_path(ip):
    path = os.path.join(_image_dir, 'cimtest_large_image')

    cmd = "dd if=/dev/zero of=%s bs=1M count=1 seek=8192" % path

    rc, out = run_remote(ip, cmd)
    if rc != 0:
        logger.error("Unable to create large disk image")
        logger.error(out)
        return None

    return path

def get_rasd_list(ip, virt, addr, disk_type):
    drasd_cn = get_typed_class(virt, "DiskResourceAllocationSettingData")

    rasds = get_default_rasds(ip, virt)

    rasd_list = {} 

    if virt == 'Xen':
        test_disk = 'xvda'
    else:
        test_disk = 'vda'

    for rasd in rasds:
        if rasd.classname == drasd_cn:
            curr_cim_rev, changeset = get_provider_version(virt, ip)
            if disk_type != "" and rasd['Caption'] != disk_type and \
               curr_cim_rev >= libvirt_cim_dasd_caption:
                continue
            rasd['Address'] = addr
            rasd['VirtualDevice'] = test_disk
        rasd_list[rasd.classname] = inst_to_mof(rasd)

    return rasd_list 

def verify_disk_path(ip, virt, addr, guest_name):
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

        if inst is None:
            raise Exception("%s instance for %s not found" % (drasd_cn, 
                            guest_name))

        if inst.Address != addr:
            raise Exception("%s instance for %s not found" % (drasd_cn, 
                            guest_name))

    except Exception, details:
        logger.error(details)
        return FAIL

    return PASS 

@do_main(sup_types)
def main():
    options = main.options

    if options.virt == "Xen":
        disk_cap = "PV disk"
    elif options.virt == "XenFV":
        disk_cap = "FV disk"
    else:
        disk_cap = "" 

    cxml = get_class(options.virt)(test_dom)

    guest_defined = False

    try:
        addr = make_long_disk_path(options.ip)
        if addr is None:
            raise Exception("Unable to create large disk image")

        rasd_list = get_rasd_list(options.ip, options.virt, addr, disk_cap)
        if len(rasd_list) < 1:
            raise Exception("Unable to get template RASDs for %s" % test_dom)

        cxml.set_res_settings(rasd_list)
        ret = cxml.cim_define(options.ip)
        if not ret:
            raise Exception("Unable to define %s" % test_dom)

        guest_defined = True 

        status = verify_disk_path(options.ip, options.virt, addr, test_dom)
        if status != PASS:
            raise Exception("Failed to verify disk path for %s" % test_dom)

    except Exception, details:
        logger.error(details)
        status = FAIL

    if addr and os.path.exists(addr):
        os.remove(addr)

    if guest_defined == True: 
        cxml.undefine(options.ip)

    return status 

if __name__ == "__main__":
    sys.exit(main())
    
