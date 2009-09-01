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
#Steps:
#1) Define 2 domains,'default' and 'test', both with random UUID
#2) Reset the uuid of the second domain, 'test', to the uuid of the
#   first domain, using ModifySystemSettings
#

import sys
import time
import pywbem
from XenKvmLib import vsms
from XenKvmLib import vxml
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from XenKvmLib.const import do_main
from XenKvmLib.classes import get_typed_class, inst_to_mof
from XenKvmLib.enumclass import GetInstance 
from XenKvmLib.const import get_provider_version

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
default_dom = 'uuid_domain'
test_dom = 'test_domain'
nmac = '99:aa:bb:cc:ee:ff'
duplicate_uuid_support = 915

def get_vssd(ip, virt, dom):
    cn = get_typed_class(virt, "VirtualSystemSettingData") 
    inst = None

    try:
        if virt == "XenFV": 
            virt = "Xen"

        key_list = {"InstanceID" : "%s:%s" % (virt, dom) }

        inst = GetInstance(ip, cn, key_list, True)

    except Exception, details:
        logger.error(details)
        return FAIL, inst

    if inst is None:
        return FAIL, inst

    return PASS, inst

@do_main(sup_types)
def main():
    options = main.options 
    virt = options.virt
    server = options.ip

    curr_cim_rev, changeset = get_provider_version(virt, server)
    if curr_cim_rev < duplicate_uuid_support:
        logger.info("Need provider version %d or greater to run testcase",
                     duplicate_uuid_support)
        return SKIP

    service = vsms.get_vsms_class(options.virt)(options.ip)
    
    sxml = None
    cxml = vxml.get_class(options.virt)(default_dom)
    ret = cxml.cim_define(options.ip)
    if not ret:
        logger.error("Failed to define the dom: %s", default_dom)
        return FAIL

    try:
        status, inst = get_vssd(options.ip, options.virt, default_dom)
        if status != PASS:
            raise Exception("Failed to get the VSSD instance for %s" % 
                             default_dom)

        uuid_defaultdom = inst['UUID']

        sxml = vxml.get_class(options.virt)(test_dom, mac=nmac)
        ret = sxml.cim_define(options.ip)
        if not ret:
            raise Exception("Failed to define the dom: %s" % test_dom)

        status, inst = get_vssd(options.ip, options.virt, test_dom)
        if status != PASS:
            raise Exception("Failed to get the VSSD instance for %s" %
                             test_dom)

        inst['UUID'] = uuid_defaultdom
        vssd = inst_to_mof(inst)
        ret = service.ModifySystemSettings(SystemSettings=vssd)
        if ret[0] == 0:
            raise Exception("Was able to assign duplicate UUID to domain %s"
                             % test_dom)

    except pywbem.CIMError, (err_no, err_desc):    
        if err_desc.find("'uuid_domain' is already defined") >= 0:
            logger.info('Got expected error desc %s', err_desc)
            status = PASS

    except Exception, details:
        logger.error("Excepttion %s", details)
        status = FAIL

    if sxml != None:
        sxml.undefine(options.ip)
    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())
 
