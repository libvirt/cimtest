#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
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
#                                             Date : 09-04-2008

import sys
import pywbem
from XenKvmLib import const
from XenKvmLib import devices
from XenKvmLib.vxml import KVMXML
from CimTest.Globals import logger
from CimTest.Globals import do_main
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC

sup_types = ['KVM']

test_dom = "test_domain"
test_mac = "00:11:22:33:44:55"
bug = '00004'

@do_main(sup_types)
def main():
    options = main.options
    cxml = KVMXML(test_dom, mac = test_mac, ntype='user')
    ret = cxml.define(options.ip)
    if not ret:
        logger.error('Unable to define domain %s' % test_dom)
        return FAIL

    devid = "%s/%s" % (test_dom, test_mac)
    key_list = { 'DeviceID' : devid,
                 'CreationClassName' : "KVM_NetworkPort",
                 'SystemName' : test_dom,
                 'SystemCreationClassName' : "KVM_ComputerSystem"
               }

    dev = None 
    try:
        dev = devices.KVM_NetworkPort(options.ip, key_list)
    except Exception, detail:
        logger.error("Exception: %s" % detail)
        cxml.undefine(options.ip)
        return XFAIL_RC(bug)

    if dev.DeviceID != devid:
        logger.error("DeviceID reported incorrectly (%s instead of %s)",
                      dev.DeviceID, devid)
        cxml.undefine(options.ip)
        return FAIL

    status = PASS
    
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

    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())
