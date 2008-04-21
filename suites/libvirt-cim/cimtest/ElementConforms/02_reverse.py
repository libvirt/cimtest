#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Veerendra Chandrappa <vechandr@in.ibm.com>
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

# This tc is used to verify the results for the assoc returned by the 
# ElemConformsToProfile for the Xen_RegdProfile Class.

# wbemcli ain -ac Xen_ElementConformsToProfile \ 
# 'http://localhost:5988/root/virt:Xen_ComputerSystem.\
# CreationClassName="Xen_ComputerSystem",Name="test-dom"'

# wbemcli ain -ac Xen_ElementConformsToProfile \
# 'http://localhost:5988/root/virt:Xen_HostSystem.\
# CreationClassName="Xen_HostSystem",Name="elm3b24.beaverton.ibm.com"'

#
# Date : 07-12-2007

import sys
from pywbem.cim_obj import CIMInstanceName
from XenKvmLib.test_xml import testxml
from VirtLib import utils
from CimTest import Globals
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE, CIM_ERROR_ASSOCIATORS 
from CimTest.Globals import do_main
from XenKvmLib import hostsystem
from XenKvmLib import computersystem
from XenKvmLib import assoc
from XenKvmLib.test_doms import destroy_and_undefine_all
from XenKvmLib.test_doms import destroy_and_undefine_all
from XenKvmLib import enumclass
from XenKvmLib.vxml import XenXML, KVMXML, get_class
from XenKvmLib.classes import get_typed_class
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'XenFV', 'KVM']

test_dom = "domgst"

def build_exp_prof_list(proflist, virt="Xen"):
    list = {} 
    
    for item in proflist:
        if item.InstanceID.find('-VirtualSystem-') >= 0:
            list[get_typed_class(virt, 'ComputerSystem')] = item 
        elif item.InstanceID.find('-SystemVirtualization-') >= 0:
            list[get_typed_class(virt, 'HostSystem')] = item 

    return list

def verify_profile(inst, exp_inst):
    if inst['InstanceID'] != exp_inst.InstanceID:
        return FAIL
    if inst['RegisteredOrganization'] != exp_inst.RegisteredOrganization:
        return FAIL
    if inst['RegisteredName'] != exp_inst.RegisteredName:
        return FAIL
    if inst['RegisteredVersion'] != exp_inst.RegisteredVersion:
        return FAIL

    return PASS 

@do_main(sup_types)
def main():
    options = main.options

    status = FAIL
    destroy_and_undefine_all(options.ip)
    virt_xml = get_class(options.virt)
    cxml = virt_xml(test_dom)

    ret = cxml.define(options.ip)
    if not ret:
        logger.error("ERROR: Failed to Define the dom: %s" % test_dom)
        return status

    inst_list = []

    try:
        cs_list = computersystem.enumerate(options.ip, options.virt)
        # The len should be atleast two, as the CS returns info
        # one regarding VS and the other one for Domain-0. 
        if len(cs_list) < 1:
            logger.error("ERROR: Wrong number of instances returned")
            return status
        for item in cs_list:
            if item.Name == test_dom:
                inst_list.append(item)
                break

        if len(inst_list) != 1:
            logger.error("ERROR: Instance for %s not created" % test_dom)
            return status

        #Getting the hostname, to verify with the value returned by the assoc.
        host_sys = hostsystem.enumerate(options.ip, options.virt)

        if len(host_sys) < 1:
            logger.error("ERROR: Enumerate returned 0 host instances")
            return status
        elif host_sys[0].Name == "":
            logger.error("ERROR: HostName seems to be empty")
            return status
        else:
            # Instance of the HostSystem
            inst_list.append(host_sys[0])
    except Exception , detail:
        logger.error("Exception: %s" % detail)
        return status

    prev_namespace = Globals.CIM_NS
    Globals.CIM_NS = 'root/interop'

    try:
        key_list = ["InstanceID"]
        proflist = enumclass.enumerate(options.ip, \
                                       "RegisteredProfile", \
                                        key_list,
                                        options.virt)
    except Exception, detail:
        logger.error(CIM_ERROR_ENUMERATE, \
                             'RegisteredProfile')
        logger.error("Exception: %s", detail)
        return status

    Globals.CIM_NS = prev_namespace

    exp_list = build_exp_prof_list(proflist, options.virt)

    # Loop through the assoc results returned on test_dom and hostsystem 
    try:
        for item in inst_list:  
            cn = item.CreationClassName
            name = item.Name
            profs = assoc.Associators(options.ip,
                                      "ElementConformsToProfile",
                                      cn,
                                      options.virt, 
                                      CreationClassName=cn,
                                      Name=name)
            if len(profs) != 1:
                logger.error("ElementConformsToProfile assoc failed")
                return status 

            status = verify_profile(profs[0], exp_list[cn])
            if status != PASS:
                logger.error("Verification of profile instance failed")

    except Exception, detail:
        logger.error(CIM_ERROR_ASSOCIATORS, 'RegisteredProfile')
        logger.error("Exception: %s", detail)
        status = FAIL

    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())

