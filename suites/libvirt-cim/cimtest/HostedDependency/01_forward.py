#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
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

# This tc is used to verify the caption, system name and the classname are 
# appropriately set for each of the domains when verified using the 
# Xen_HostedDependency asscoiation.
#
# Example cli command is 
# wbemcli ain -ac Xen_HostedDependency 
# 'http://localhost:5988/root/virt:Xen_ComputerSystem.CreationClassName=
# "Xen_ComputerSystem",Name="hd_domain"' -nl
#
# The output should be a single record and it will look something like this:
# localhost:5988/root/virt:Xen_HostSystem.CreationClassName="Xen_HostSystem",
# Name="mx3650b.in.ibm.com"
# ......
# -CommunicationStatus
# -CreationClassName="Xen_HostSystem"
# -Name="mx3650b.in.ibm.com"
# -PrimaryOwnerName
# -PrimaryOwnerContact
# -Roles
# .....
#  
#                                                Date : 20-11-2007

import sys
import pywbem
from VirtLib import utils
from XenKvmLib import vxml
from XenKvmLib import computersystem 
from XenKvmLib import assoc
from XenKvmLib import enumclass
from XenKvmLib.classes import get_class_basename
from CimTest import Globals
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom = "hd_domain"
test_mac = "00:11:22:33:44:55"

@do_main(sup_types)
def main():
    options = main.options
    status = PASS

    virtxml = vxml.get_class(options.virt)
    if options.virt == "LXC":
        cxml = virtxml(test_dom)
    else:
        cxml = virtxml(test_dom, mac = test_mac)
    ret = cxml.define(options.ip)
    if not ret:
        Globals.logger.error("Failed to Create the dom: %s", test_dom)
        status = FAIL
        return status
    keys = ['Name', 'CreationClassName']
    try:
        host = enumclass.enumerate(options.ip, 'HostSystem', keys, options.virt)[0]
    except Exception,detail:
        Globals.logger.error(Globals.CIM_ERROR_ENUMERATE, 'Hostsystem')
        Globals.logger.error("Exception: %s", detail)
        status = FAIL
        cxml.undefine(options.ip)
        return status

    try: 
        cs = computersystem.enumerate(options.ip, options.virt)
    except Exception,detail:
        Globals.logger.error(Globals.CIM_ERROR_ENUMERATE, 'ComputerSystem')
        Globals.logger.error("Exception: %s", detail)
        status = FAIL
        cxml.undefine(options.ip)
        return status
    
    hs_cn = "HostedDependency"
    try:
        for system in cs:
            ccn = get_class_basename(system.CreationClassName)
            hs = assoc.Associators(options.ip, hs_cn, ccn, options.virt,
                                   CreationClassName=system.CreationClassName,
                                   Name=system.name)

            if not hs:
                cxml.undefine(options.ip)
                Globals.logger.error("HostName seems to be empty")
                status = FAIL
                break

            if len(hs) != 1:
                test =  "(len(hs), system.name)"
                Globals.logger.error("HostedDependency returned %i HostSystem \
objects for domain '%s'", len(hs), system.name)
                status = FAIL
                break

            cn = hs[0]["CreationClassName"]
            sn = hs[0]["Name"]

            if cn != host.CreationClassName:
                Globals.logger.error("CreationClassName does not match")
                status = FAIL
                
            if sn != host.Name:
                Globals.logger.error("Name does not match")
                status = FAIL

            if status != 0:
                break
            
    except Exception,detail:
        Globals.logger.error(Globals.CIM_ERROR_ASSOCIATORS, hs_cn)
        Globals.logger.error("Exception: %s", detail)
        status = FAIL
        cxml.undefine(options.ip)
        return status

    cxml.undefine(options.ip)
    return status
    
if __name__ == "__main__":
    sys.exit(main())
