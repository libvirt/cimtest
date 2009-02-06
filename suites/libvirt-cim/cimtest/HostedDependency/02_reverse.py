#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
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

# This tc is used to verify the hostname and the classname are appropriately
# set for each of the domains when verified using the Xen_HostedDependency 
# asscoiation.
#
# Example cli command is 
# wbemcli ain -ac Xen_HostedDependency 
# 'http://localhost:5988/root/virt:
# Xen_HostSystem.CreationClassName="Xen_HostSystem",Name="3650b"'
#
# For which we get the following output
# localhost:5988/root/virt:Xen_ComputerSystem.
# CreationClassName="Xen_ComputerSystem",Name="xen1"
#
# localhost:5988/root/virt:Xen_ComputerSystem.
# CreationClassName="Xen_ComputerSystem",Name="Domain-0"  
#
#                                                Date : 15-11-2007

import sys
from VirtLib import utils
from XenKvmLib import vxml
from XenKvmLib import enumclass
from XenKvmLib import assoc
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.common_util import get_host_info, call_request_state_change

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom = "hd_domain"
test_mac = "00:11:22:33:44:55"
TIME = "00000000000000.000000:000"

@do_main(sup_types)
def main():
    options = main.options
    virt = options.virt
    server = options.ip
    status = PASS

    virtxml = vxml.get_class(virt)
    if virt == "LXC":
       cxml = virtxml(test_dom)
    else:
       cxml = virtxml(test_dom, mac = test_mac)

    ret = cxml.cim_define(server)
    if not ret:
        logger.error("Failed to define the dom: %s", test_dom)
        return FAIL

    rc = call_request_state_change(test_dom, server, 2, TIME, virt)
    if rc != 0:
        logger.error("Failed to start the dom: %s", test_dom)
        cxml.undefine(server)
        return FAIL

    try:
        status, host_inst = get_host_info(server, virt)
        if status != PASS:
            cxml.destroy(server)
            cxml.undefine(server)
            return status

        host_ccn = host_inst.CreationClassName
        host_name = host_inst.Name

        cs_class = get_typed_class(options.virt, 'ComputerSystem')
        cs = enumclass.EnumInstances(server, cs_class)
        if virt == 'Xen' or options.virt == 'XenFV':
            # Xen honors additional domain-0
            cs_list_len = 2
        else:
            cs_list_len = 1
        if len(cs) < cs_list_len:
            raise Exception("Wrong number of systems returned")
       
        # Build a list of ComputerSystem names from the list returned from
        # ComputerSystem.EnumerateInstances()
        cs_names = [x.name for x in cs]

        assoc_cn = get_typed_class(virt, "HostedDependency")   
         
        # Get a list of ComputerSystem instances from the HostSystem instace
        systems = assoc.AssociatorNames(server, assoc_cn, host_ccn,
                                        CreationClassName=host_ccn,
                                        Name=host_name)


        # Compare each returned instance to make sure it's in the list
        # that ComputerSystem.EnumerateInstances() returned
        if len(systems) < 1:
            logger.error("HostedDependency returned %d, expected at least 1",
                          len(systems))
            cxml.destroy(server)
            cxml.undefine(server)

        ccn = cs[0].CreationClassName
        for guest in systems:
            if guest["Name"] in cs_names:
                cs_names.remove(guest["Name"])
            else:
                logger.error("HostedDependency returned unexpected guest %s",
                             guest["Name"])
                status = FAIL

        # checking the CreationClassName returned is Xen_ComputerSystem
            if ccn != guest["CreationClassName"]:
                logger.error("CreationClassName does not match")
                status = FAIL

        # Go through anything remaining in the
        # ComputerSystem.EnumerateInstances() list and complain about them
        # not being returned by HostedDependency

        for guest in cs_names:
            logger.error("HostedDependency did not return expected guest %s",
                         guest["Name"])
            status = FAIL
            
    except Exception, detail:
        logger.error("Exception: %s", detail)
        status = FAIL

    cxml.destroy(server)
    cxml.undefine(server)
    return status

if __name__ == "__main__":
    sys.exit(main())
