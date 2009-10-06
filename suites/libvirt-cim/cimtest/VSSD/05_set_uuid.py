#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
#
# Authors:
#    Yogananth Subramanian <anantyog@linux.vnet.ibm.com>
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
#This test defines a domain with user specified UUID
#

import sys
from XenKvmLib.test_doms import set_uuid
from XenKvmLib import vsms
from XenKvmLib import vxml
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from XenKvmLib.const import do_main, get_provider_version
from XenKvmLib.classes import get_typed_class
from XenKvmLib.enumclass import GetInstance 

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
default_dom = 'uuid_domain'
uuid = set_uuid()
uuid_changes = 873

def get_vssd(ip, virt, get_cim_inst):
    cn = get_typed_class(virt, "VirtualSystemSettingData") 
    inst = None

    try:
        if virt == "XenFV": 
            virt = "Xen"

        key_list = {"InstanceID" : "%s:%s" % (virt, default_dom) }
        inst = GetInstance(ip, cn, key_list, get_cim_inst)

    except Exception, details:
        logger.error(details)
        return FAIL, inst

    if inst is None:
        return FAIL, inst

    return PASS, inst

@do_main(sup_types)
def main():
    options = main.options 

    cim_rev, changeset = get_provider_version(options.virt, options.ip)
    if cim_rev < uuid_changes:
        logger.info("UUID attribute added VSSD in libvirt-cim version '%s'",
                    uuid_changes)
        return SKIP

    service = vsms.get_vsms_class(options.virt)(options.ip)

    cxml = vxml.get_class(options.virt)(default_dom, uuid=uuid)
    ret = cxml.cim_define(options.ip)
    if not ret:
        logger.error("Failed to define the dom: %s", default_dom)
        return FAIL

    try:
        status, inst = get_vssd(options.ip, options.virt, True)
        if status != PASS:
            raise Exception("Failed to get the VSSD instance for %s"% 
                             default_dom)

        if inst['UUID'] != uuid:
            raise Exception(" UUID is differnet from the one set by the user")
        else:
            logger.info("UUID is same as the one set by the user")

    except Exception, details:
        logger.error(details)
        status = FAIL

    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())
 
