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
from XenKvmLib.const import do_main
from XenKvmLib import enumclass
from XenKvmLib import assoc
from XenKvmLib.test_doms import destroy_and_undefine_all
from XenKvmLib.test_doms import destroy_and_undefine_all
from XenKvmLib import enumclass
from XenKvmLib.vxml import XenXML, KVMXML, get_class
from XenKvmLib.classes import get_typed_class
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.common_util import libvirt_cached_data_poll, get_cs_instance 

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']

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

    rc, cs = get_cs_instance(test_dom, options.ip, options.virt)
    if rc != 0:
        sys = libvirt_cached_data_poll(options.ip, options.virt, test_dom)
        if sys is None:
            logger.error("Instance for %s not created" % test_dom)
            return FAIL 

        inst_list.append(sys)
    keys = ['Name', 'CreationClassName']
    try:
        #Getting the hostname, to verify with the value returned by the assoc.
        cn = get_typed_class(options.virt, 'HostSystem')
        host_sys = enumclass.EnumInstances(options.ip, cn)

        if len(host_sys) < 1:
            logger.error("ERROR: Enumerate returned 0 host instances")
            return FAIL 

        inst_list.append(host_sys[0])

    except Exception, details:
        logger.error("Exception: %s" % details)
        return FAIL 

    prev_namespace = Globals.CIM_NS
    Globals.CIM_NS = 'root/interop'

    try:
        cn = get_typed_class(options.virt, 'RegisteredProfile')
        proflist = enumclass.EnumInstances(options.ip, cn)
    except Exception, details:
        logger.error(CIM_ERROR_ENUMERATE, cn) 
        logger.error("Exception: %s", details)
        return status

    Globals.CIM_NS = prev_namespace

    exp_list = build_exp_prof_list(proflist, options.virt)

    # Loop through the assoc results returned on test_dom and hostsystem 
    try:
        for item in inst_list:  
            cn = item.CreationClassName
            name = item.Name
            an = get_typed_class(options.virt, "ElementConformsToProfile")
            profs = assoc.Associators(options.ip,
                                      an,
                                      cn,
                                      CreationClassName=cn,
                                      Name=name)
            if len(profs) != 1:
                logger.error("ElementConformsToProfile assoc failed")
                return FAIL

            status = verify_profile(profs[0], exp_list[cn])
            if status != PASS:
                logger.error("Verification of profile instance failed")
                return FAIL

    except Exception, detail:
        logger.error(CIM_ERROR_ASSOCIATORS, 
                     get_typed_class(options.virt, 'RegisteredProfile'))
        logger.error("Exception: %s", detail)
        status = FAIL

    cxml.undefine(options.ip)
    return status

if __name__ == "__main__":
    sys.exit(main())

