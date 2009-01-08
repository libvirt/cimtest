#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
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

sup_types = ['Xen', 'XenFV', 'KVM']
default_dom = "diskrasd_test"

import sys

from CimTest.ReturnCodes import FAIL, PASS
from XenKvmLib.const import do_main
from CimTest.Globals import logger
from VirtLib import utils
from XenKvmLib import enumclass
from XenKvmLib.classes import get_typed_class
from XenKvmLib.vxml import get_class 

def make_image(ip, size):
    s, fn = utils.run_remote(ip, "mktemp")
    if s != 0:
        return None

    s, _ = utils.run_remote(ip,
                            "dd if=/dev/zero of=%s bs=1 count=%i" % (fn, size))
    if s != 0:
        return None

    return fn

def kill_image(ip, name):
    s, _ = utils.run_remote(ip, "rm -f %s" % name)

    return s == 0

def check_rasd_size(rasd, size):
    if rasd["AllocationUnits"] != "Bytes":
        logger.error("Got %s units, exp Bytes", rasd["AllocationUnits"])
        return FAIL

    try:
        cim_size = int(rasd["VirtualQuantity"])
    except Exception, details:
        logger.error("Failed to get DiskRASD size: %s" % details)
        return FAIL

    if cim_size != size:
        logger.error("CIM reports %i bytes, but should be %i bytes", cim_size,
                     size)
        return FAIL

    logger.info("Verified %i bytes" % cim_size)
    return PASS

@do_main(sup_types)
def main():
    options = main.options

    test_size = 123 << 10

    temp = make_image(options.ip, test_size)
    if not temp:
        logger.error("Unable to create a temporary disk image")
        return FAIL

    logger.info("Created temp disk %s of size %i bytes" % (temp, test_size))
   
    virtxml = get_class(options.virt)
    cxml = virtxml(default_dom, mem=32, disk_file_path=temp, disk="hda")

    try:
        ret = cxml.cim_define(options.ip)
        if not ret:
            raise Exception("Failed to define the dom: %s" % default_dom)

        cn = get_typed_class(options.virt, 'DiskResourceAllocationSettingData') 
        rasds = enumclass.EnumInstances(options.ip, cn, ret_cim_inst=True)

        status = FAIL
        for rasd in rasds:
            if rasd["Address"] == temp:
                status = check_rasd_size(rasd, test_size)
                break

    except Exception, details:
        logger.error("Failed to test RASD: %s" % details)
        status = FAIL

    kill_image(options.ip, temp)
    cxml.undefine(options.ip)

    return status

if __name__ == "__main__":
    sys.exit(main())
