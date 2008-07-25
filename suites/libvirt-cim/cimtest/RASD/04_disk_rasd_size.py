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
from CimTest.Globals import do_main
from CimTest.Globals import logger
from VirtLib import utils
from XenKvmLib.test_doms import undefine_test_domain
from XenKvmLib.common_util import create_using_definesystem
from XenKvmLib import vsms
from XenKvmLib import enumclass

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
        logger.error("AllocationUnits != Bytes?")
        return FAIL

    try:
        cim_size = int(rasd["VirtualQuantity"])
    except Exception, e:
        logger.error("Failed to get DiskRASD size: %s" % e)
        return FAIL

    if cim_size != size:
        logger.error("CIM reports %i bytes, but should be %i bytes" % (cim_size,
                                                                       size))
        return FAIL
    else:
        logger.info("Verified %i bytes" % cim_size)
        return PASS

def test_rasd(options, temp, test_size):
    vssd_class = vsms.get_vssd_class(options.virt)
    vssd = vssd_class(name=default_dom, virt=options.virt)

    drasd_class = vsms.get_dasd_class(options.virt)
    drasd = drasd_class("hda", temp, default_dom)

    mrasd_class = vsms.get_masd_class(options.virt)
    mrasd = mrasd_class(32, default_dom)

    params = {
        "vssd" : vssd.mof(),
        "rasd" : [drasd.mof(), mrasd.mof()]
        }

    create_using_definesystem(default_dom,
                              options.ip,
                              params=params,
                              virt=options.virt)
    
    rasds = enumclass.enumerate_inst(options.ip, drasd_class, options.virt)

    status = FAIL
    for rasd in rasds:
        if rasd["Address"] == temp:
            status = check_rasd_size(rasd, test_size)
            break

    return status

@do_main(sup_types)
def main():
    options = main.options

    test_size = 123 << 10

    temp = make_image(options.ip, test_size)
    if not temp:
        logger.error("Unable to create a temporary disk image")
        return FAIL

    logger.info("Created temp disk %s of size %i bytes" % (temp, test_size))

    try:
        status = test_rasd(options, temp, test_size)
    except Exception, e:
        logger.error("Failed to test RASD: %s" % e)

    undefine_test_domain(default_dom, options.ip, options.virt)
    kill_image(options.ip, temp)

    return status

if __name__ == "__main__":
    sys.exit(main())
