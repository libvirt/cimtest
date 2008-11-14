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
# Name="x3650"
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
from XenKvmLib import assoc
from XenKvmLib import enumclass
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import CIM_ERROR_ENUMERATE, CIM_ERROR_ASSOCIATORS, logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.common_util import get_host_info

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

test_dom = "hd_domain"
test_mac = "00:11:22:33:44:55"

@do_main(sup_types)
def main():
    options = main.options
    server = options.ip
    virt   = options.virt
    status = PASS

    virtxml = vxml.get_class(virt)
    if virt == "LXC":
        cxml = virtxml(test_dom)
    else:
        cxml = virtxml(test_dom, mac = test_mac)
    ret = cxml.define(server)
    if not ret:
        logger.error("Failed to define the dom: %s", test_dom)
        status = FAIL
        return status

    status, host_inst = get_host_info(server, virt)
    if status != PASS:
        cxml.undefine(server)
        return status

    host_ccn = host_inst.CreationClassName
    host_name = host_inst.Name
    cs_class = get_typed_class(options.virt, 'ComputerSystem')
    try: 
        cs = enumclass.EnumInstances(server, cs_class)
    except Exception,detail:
        logger.error(CIM_ERROR_ENUMERATE, cs_class)
        logger.error("Exception: %s", detail)
        cxml.undefine(server)
        return FAIL
    
    hs_cn = get_typed_class(virt, "HostedDependency")
    try:
        for system in cs:
            ccn = system.CreationClassName
            hs = assoc.Associators(server, hs_cn, ccn, 
                                   CreationClassName=ccn,
                                   Name=system.name)

            if not hs:
                cxml.undefine(server)
                logger.error("HostName seems to be empty")
                status = FAIL
                break

            if len(hs) != 1:
                test =  "(len(hs), system.name)"
                logger.error("'%s' returned %i HostSystem " 
                             "objects for domain '%s'", 
                              hs_cn, len(hs), system.name)
                status = FAIL
                break

            cn = hs[0]["CreationClassName"]
            sn = hs[0]["Name"]

            if cn != host_ccn:
                logger.error("CreationClassName does not match")
                status = FAIL
                
            if sn != host_name:
                logger.error("Name does not match")
                status = FAIL

            if status != PASS:
                break
            
    except Exception,detail:
        logger.error(CIM_ERROR_ASSOCIATORS, hs_cn)
        logger.error("Exception: %s", detail)
        cxml.undefine(server)
        return FAIL

    cxml.undefine(server)
    return status
    
if __name__ == "__main__":
    sys.exit(main())
