#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Veerendra Chandrappa <vechandr@in.ibm.com>
#    Zhengang Li <lizg@cn.ibm.com>
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

# This test case is used to verify the BootLoader property of VSSD class for VS
# Date : 25-10-2007 

import sys
from XenKvmLib import enumclass
from VirtLib import utils
from VirtLib.live import bootloader
from XenKvmLib.test_doms import test_domain_function, destroy_and_undefine_all
from XenKvmLib.test_xml import testxml_bl
from CimTest.Globals import logger
from XenKvmLib.const import do_main

sup_types = ['Xen']
test_dom = "dom"


@do_main(sup_types)
def main():
    options = main.options
    status = 1
    destroy_and_undefine_all(options.ip)

    xmlfile = testxml_bl(test_dom, server = options.ip, gtype = 0)

    ret = test_domain_function(xmlfile, options.ip, "define")
    if not ret :
        logger.error("error while 'define' of VS")
        return 1

    instIdval = "%s:%s" % (options.virt, test_dom)
    keyname = "InstanceID"
    bootldr = bootloader(server = options.ip, gtype = 0)

    try:
        key_list = { 'InstanceID' : instIdval }
        system = enumclass.getInstance(options.ip, \
                 enumclass.Xen_VirtualSystemSettingData, key_list)

        name = system.ElementName
        if name == test_dom :
            if system.Bootloader == bootldr :
                logger.info("BootLoader for domain %s is %s" % (name, bootldr ))
                status = 0
            else:
                logger.error("Bootloader is not set for VS %s" % test_dom)
                status = 1

    except  BaseException, detail :
        logger.error("Exception : %s" % detail)
        status = 1
    
    test_domain_function(test_dom, options.ip, "undefine")

    return status

if __name__ == "__main__":
    sys.exit(main())

