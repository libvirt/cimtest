#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
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

# This tc is used to verify the properties returned by the CIM_NetworkPort 
# class.
#                  
#                                             Date : 24-10-2007

import sys
import pywbem
from VirtLib import utils
from VirtLib import live
from XenKvmLib import devices
from XenKvmLib.classes import get_typed_class
from XenKvmLib.vxml import XenXML, KVMXML, get_class
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC
from XenKvmLib.const import get_provider_version 

sup_types = ['Xen', 'KVM', 'XenFV']

test_dom = "test_domain"
test_mac = "00:11:22:33:44:55"

def get_linktech(ip, virt):
    rev, changeset = get_provider_version(virt, ip)

    net_rev = 599

    # The value of LinkTechnology should be set to 0 for rev > 599
    # else, it should be set to 2
    if net_rev > rev:
        return 0
    else:
        return 2


@do_main(sup_types)
def main():
    options = main.options
    
    vsxml = get_class(options.virt)(test_dom, mac=test_mac)
    vsxml.define(options.ip)

    devid = "%s/%s" % (test_dom, test_mac)
    key_list = { 'DeviceID' : devid,
                 'CreationClassName' : get_typed_class(options.virt, "NetworkPort"),
                 'SystemName' : test_dom,
                 'SystemCreationClassName' : get_typed_class(options.virt, "ComputerSystem")
               }

    dev = None 

    try:
        dev = eval('devices.' + get_typed_class(options.virt, "NetworkPort"))(options.ip, key_list)

    except Exception, detail:
        logger.error("Exception: %s" % detail)
        vsxml.undefine(options.ip)
        return FAIL

    if dev.DeviceID == None:
        logger.error("Error retrieving instance for devid %s" % devid)
        vsxml.undefine(options.ip)
        return FAIL

    status = PASS

    link_tech = get_linktech(options.ip, options.virt)
    
    if dev.LinkTechnology != link_tech:
        logger.error("LinkTechnology should be set to `%i' instead of `%s'" % \
              (link_tech, dev.LinkTechnology))
        status = FAIL

    addrs = dev.NetworkAddresses
    if len(addrs) != 1:
        logger.error("Too many NetworkAddress entries (%i instead of %i)" % \
              (len(addrs), 1))
        status = FAIL
        
    if addrs[0] != test_mac:
        logger.error("MAC address reported incorrectly (%s instead of %s)" % \
              (addrs[0], test_mac))
        status = FAIL

    if status == FAIL:
        logger.error("Checked interface %s" % test_mac)

    vsxml.undefine(options.ip)
    
    return status

if __name__ == "__main__":
    sys.exit(main())
    
