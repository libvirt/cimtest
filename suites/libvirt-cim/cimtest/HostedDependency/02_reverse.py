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
# Xen_HostSystem.CreationClassName="Xen_HostSystem",Name="mx3650b.in.ibm.com"'
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
from XenKvmLib import hostsystem
from XenKvmLib import computersystem 
from XenKvmLib import assoc
from XenKvmLib.classes import get_class_basename
from CimTest.Globals import logger, do_main
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM']

test_dom = "hd_domain"
test_mac = "00:11:22:33:44:55"

@do_main(sup_types)
def main():
    options = main.options
    status = PASS

    virtxml = vxml.get_class(options.virt)
    cxml = virtxml(test_dom, mac = test_mac)
    ret = cxml.create(options.ip)

    if not ret:
        logger.error("ERROR: Failed to Create the dom: %s" % test_dom)
        status = FAIL
        return status

    try:
        host_sys = hostsystem.enumerate(options.ip, options.virt)
        if host_sys[0].Name == "":
            raise Exception("HostName seems to be empty")
        else:
        # Instance of the HostSystem
            host_sys = host_sys[0]

        cs = computersystem.enumerate(options.ip, options.virt)
        if options.virt == 'Xen' or options.virt == 'XenFV':
            # Xen honors additional domain-0
            cs_list_len = 2
        else:
            cs_list_len = 1
        if len(cs) < cs_list_len:
            raise Exception("Wrong number of systems returned")
       
        # Build a list of ComputerSystem names from the list returned from
        # ComputerSystem.EnumerateInstances()
        cs_names = [x.name for x in cs]

        # Get a list of ComputerSystem instances from the HostSystem instace
        host_ccn = host_sys.CreationClassName
        systems = assoc.AssociatorNames(options.ip, "HostedDependency",
                                        get_class_basename(host_ccn), 
                                        options.virt,
                                        CreationClassName=host_ccn,
                                        Name=host_sys.Name)

        # Compare each returned instance to make sure it's in the list
        # that ComputerSystem.EnumerateInstances() returned
        if len(systems) < 1:
            raise Exception("HostedDependency returned %d, expected at least 1" %
                            len(systems))

        ccn = cs[0].CreationClassName
        for guest in systems:
            if guest["Name"] in cs_names:
                cs_names.remove(guest["Name"])
            else:
                logger.error("HostedDependency returned unexpected guest %s" %
                             guest["Name"])
                status = FAIL

        # checking the CreationClassName returned is Xen_ComputerSystem
            if ccn != guest["CreationClassName"]:
                logger.error("ERROR: CreationClassName does not match")
                status = FAIL

        # Go through anything remaining in the
        # ComputerSystem.EnumerateInstances() list and complain about them
        # not being returned by HostedDependency

        for guest in cs_names:
            logger.error("HostedDependency did not return expected guest %s" %
                         guest["Name"])
            status = FAIL
            
    except (UnboundLocalError, NameError), detail:
        logger.error("Exception: %s" % detail)
    
    except Exception, detail:
        logger.error(detail)
        status = FAIL

    cxml.destroy(options.ip)
    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())
