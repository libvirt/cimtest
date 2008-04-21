#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
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

import sys
import pywbem
from VirtLib import utils
from VirtLib import live
from XenKvmLib import devices
from XenKvmLib.classes import get_typed_class
from XenKvmLib.vxml import XenXML, KVMXML, get_class
from XenKvmLib.test_doms import define_test_domain, undefine_test_domain
from XenKvmLib.test_xml import testxml
from CimTest.Globals import logger, do_main

sup_types = ['Xen', 'KVM', 'XenFV']

test_dom = "test_domain"
def clean_system(host, virt='Xen'):
    l = live.domain_list(host, virt)
    if len(l) > 1:
        return False
    else:
        return True

@do_main(sup_types)
def main():
    options = main.options
    if not clean_system(options.ip, options.virt):
        logger.error("System has defined domains; unable to run")
        return 2

    if options.virt == 'Xen':
        test_dev = 'xvda'
    else:
        test_dev = 'hda'

    vsxml = get_class(options.virt)(test_dom, disk=test_dev)
    ret = vsxml.define(options.ip)
    if not ret:
        logger.error("Failed to Define the dom: %s", test_dom)
        return FAIL

    devid = "%s/%s" % (test_dom, test_dev)

    status = 0
    key_list = ["DeviceID", "CreationClassName", "SystemName", "SystemCreationClassName"]

    devs = devices.enumerate(options.ip, 'LogicalDisk', key_list)
    if devs.__class__ == str:
        logger.error("Got error instead of empty list: %s" % devs)
        status = 1    

    vsxml.undefine(options.ip)
    
    return status

if __name__ == "__main__":
    sys.exit(main())
    
