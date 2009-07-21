#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <deeptik@linux.vnet.ibm.com>
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
# This test case verifies that, if user does not specify MAC Address, 
# a MAC address is generated for the domain by the provider.
#                                                   Date: 21-07-2009                              
# 

import sys
from XenKvmLib.const import do_main
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.vxml import get_class
from XenKvmLib.enumclass import EnumInstances
from XenKvmLib.classes import get_typed_class

SUPPORTED_TYPES = ['Xen', 'KVM', 'XenFV', 'LXC']
default_dom = 'dom_mac_notspecified'
MAC_ADDR_LEN = 6 


def verify_nrasd_mac_value(virt, server):
    rasd_list   = []
    classname = get_typed_class(virt, "NetResourceAllocationSettingData")
    try:
        rasd_list = EnumInstances(server, classname, ret_cim_inst=True)
        if len(rasd_list) < 1:
            logger.error("%s returned %i instances, excepted at least 1.",
                         classname, len(rasd_list))
            return FAIL

        for rasd in rasd_list:
            # Verify the Mac Address for the domain is generated and set
            if default_dom in rasd['InstanceID']:
                mac_addr_len = len(rasd['Address'].split(":"))
                if rasd['Address'] != "" and mac_addr_len == MAC_ADDR_LEN:
                    logger.info("Mac Address for dom '%s' is set to '%s'", \
                                 default_dom, rasd['Address'])
                    return PASS

    except Exception, detail:
        logger.error("Exception: %s", detail)
        return FAIL

    logger.error("Mac Address for dom '%s' is not set", default_dom)
    return FAIL

@do_main(SUPPORTED_TYPES)
def main():
    options = main.options

    cxml = get_class(options.virt)(default_dom, mac=None)
 
    try:
        ret = cxml.cim_define(options.ip)
        if not ret:
            raise Exception("Unable to define %s" % default_dom)

        status = cxml.cim_start(options.ip)
        if status != PASS:
            cxml.undefine(options.ip)
            raise Exception("Failed to start the defined domain: %s" \
                             % default_dom) 

        status = verify_nrasd_mac_value(options.virt, options.ip)

    except Exception, details:
        logger.error("Exception details: %s", details)
        return FAIL

    cxml.cim_destroy(options.ip)
    cxml.undefine(options.ip)

    return status

if __name__ == "__main__":
    sys.exit(main())

