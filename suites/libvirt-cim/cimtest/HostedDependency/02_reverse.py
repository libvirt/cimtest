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
from XenKvmLib.test_xml import testxml
from VirtLib import utils
from XenKvmLib import hostsystem
from XenKvmLib import computersystem 
from XenKvmLib import assoc
from XenKvmLib.test_doms import test_domain_function
from CimTest.Globals import log_param, logger, do_main

sup_types = ['Xen']

test_dom = "hd_domain"
test_mac = "00:11:22:33:44:55"

@do_main(sup_types)
def main():
    options = main.options
    log_param()
    status = 0

    test_xml = testxml(test_dom, mac = test_mac)
    ret = test_domain_function(test_xml, options.ip, cmd = "create")

    if not ret:
        logger.error("ERROR: Failed to Create the dom: %s" % test_dom)
        status = 1
        return status

    try:
        host_sys = hostsystem.enumerate(options.ip)
        if host_sys[0].Name == "":
            ret = test_domain_function(test_dom, options.ip, \
                                                            cmd = "destroy")
            logger.error("ERROR: HostName seems to be empty")
            status = 1
            return status
        else:
        # Instance of the HostSystem
            host_sys = host_sys[0]

        cs = computersystem.enumerate(options.ip)
        # The len should be atleast two , bcs the CS returns info
        # one regd VS and the other one for Dom-0 
        if len(cs) < 2:
            logger.error("ERROR: Wrong number of systems returned")
            status = 1 
            return status
       
        # Build a list of ComputerSystem names from the list returned from
        # ComputerSystem.EnumerateInstances()
        cs_names = []
        for inst in cs:
            cs_names.append(inst.name)
        # Store the Creation classname 
        ccn = cs[0].CreationClassName

        # Get a list of ComputerSystem instances from the HostSystem instace
        host_ccn = host_sys.CreationClassName
        systems = assoc.AssociatorNames(options.ip,
                                        "Xen_HostedDependency",
                                        host_ccn, 
                                        CreationClassName = host_ccn,
                                        Name=host_sys.Name)

        # Compare each returned instance to make sure it's in the list
        # that ComputerSystem.EnumerateInstances() returned
        if len(systems) < 1:
            logger.error("HostedDependency returned %d, expected at least 1" %
                         len(systems))
            test_domain_function(test_dom, options.ip, cmd = "destroy")
            return 1

        for guest in systems:
            if guest["Name"] in cs_names:
                cs_names.remove(guest["Name"])
            else:
                logger.error("HostedDependency returned unexpected guest %s" %
                             guest["Name"])
                status = 1

        # checking the CreationClassName returned is Xen_ComputerSystem
            if ccn != guest["CreationClassName"]:
                logger.error("ERROR: CreationClassName does not match")
                status = 1

        # Go through anything remaining in the
        # ComputerSystem.EnumerateInstances() list and complain about them
        # not being returned by HostedDependency

        for guest in cs_names:
            logger.error("HostedDependency did not return expected guest %s" %
                         guest["Name"])
            status = 1
            
    except (UnboundLocalError, NameError), detail:
        logger.error("Exception: %s" % detail)

    ret = test_domain_function(test_dom, options.ip, cmd = "destroy") 
    return status
if __name__ == "__main__":
    sys.exit(main())
