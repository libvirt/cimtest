#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
#
# Authors:
#    Sharad Mishra <snmishra@us.ibm.com>
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
# This test case is used to verify IPv6 support. It verifies that if an IP 
# address is supplied, that address gets used for VNC. If an address is not 
# supplied then the new is_ipv6_only flag is read. If the flag is set, then
# default ipv6 address is used. Else default ipv4 address gets used.
# This test case:
#
# Defines a guest in a loop with different settings of IP 
# address and is_ipv6_only flag.
#
# Once the guest is defined, gets the instance of DisplayController
# and GRASD.
# Checks to make sure expected vnc address is set for both.
#
#                                               Date : Nov. 11, 2009
#

import sys
from XenKvmLib.enumclass import GetInstance
from XenKvmLib.vxml import get_class
from XenKvmLib.classes import get_typed_class
from XenKvmLib.const import do_main, get_provider_version
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL, SKIP

sup_types = ['Xen', 'KVM', 'XenFV']
libvirtcim_redSAP_changes = 1017
test_dom = 'test_ipv6_dom'

address_dict = {('127.0.0.1', None)     : '127.0.0.1:-1',
                ('[::1]', None)         : '[::1]:-1',
                ('127.0.0.1', True)     : '127.0.0.1:-1',
                ('[::1]', False)        : '[::1]:-1',
                ('127.0.0.1', False)    : '127.0.0.1:-1',
                ('[::1]', True)         : '[::1]:-1',
                (None, True)            : '[::1]:-1',
                (None, False)           : '127.0.0.1:-1',
                (None, None)            : '127.0.0.1:-1'
               }

@do_main(sup_types)
def main():
    status = PASS
    virt = main.options.virt
    server = main.options.ip

    cname = 'KVMRedirectionSAP'
    classname = get_typed_class(virt, cname)

    # This check is required for libvirt-cim providers which do not have 
    # REDSAP changes in it and the REDSAP provider is available with 
    # revision >= 1017.
    curr_cim_rev, changeset = get_provider_version(virt, server)
    if curr_cim_rev  < libvirtcim_redSAP_changes:
        logger.info("'%s' provider not supported, hence skipping the tc ....",
                    classname)
        return SKIP 

    vsxml = None

    try:
        virt_xml =  get_class(virt)
        for key, value in address_dict.iteritems():
            add = key[0]
            flg = key[1]
            if add == None:
                vsxml = virt_xml(test_dom, is_ipv6_only=flg)
            else:
                vsxml = virt_xml(test_dom, address=add, is_ipv6_only=flg)
            # Define the VS
            ret = vsxml.cim_define(server)
            if not ret:
                raise Exception("Failed to define the dom: %s" % test_dom)

            devid = "%s/%s" % (test_dom, 'vnc')
            vnc = get_typed_class(virt, "DisplayController")
            key_list = { 'DeviceID' : devid,
                         'CreationClassName' : vnc,
                         'SystemName' : test_dom,
                         'SystemCreationClassName' : 
                         get_typed_class(virt, "ComputerSystem")
                       }
            dev = GetInstance(server, vnc, key_list)
            vp = "vnc/%s" % value

            if vp != dev.VideoProcessor:
                vsxml.undefine(server)
                raise Exception("Unxpected VNC server address")

            vnc = get_typed_class(virt, "GraphicsResourceAllocationSettingData")
            key_list = { 'InstanceID' : devid,
                         'CreationClassName' : vnc,
                         'SystemName' : test_dom,
                         'SystemCreationClassName' : 
                         get_typed_class(virt, "ComputerSystem")
                       }
            dev = GetInstance(server, vnc, key_list)

            if value != dev.Address:
                vsxml.undefine(server)
                raise Exception("Unxpected VNC server address")

            vsxml.undefine(server)
    		 		 
    except Exception, detail:
        logger.error("Exception: %s", detail)
        status = FAIL

    return status

if __name__ == "__main__":
    sys.exit(main())
