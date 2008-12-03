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
# CreationClassName="Xen_HostSystem",Name="lm3b24"'

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
from XenKvmLib import enumclass
from XenKvmLib.vxml import XenXML, KVMXML, get_class
from XenKvmLib.classes import get_typed_class
from CimTest.ReturnCodes import PASS, FAIL, XFAIL_RC
from XenKvmLib.common_util import libvirt_cached_data_poll, get_cs_instance, \
                                  get_host_info

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']

test_dom  ="domgst"
bug_sblim ='00007'

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
    server = options.ip
    virt   = options.virt

    status = FAIL
    destroy_and_undefine_all(server)
    virt_xml = get_class(virt)
    cxml = virt_xml(test_dom)

    ret = cxml.cim_define(server)
    if not ret:
        logger.error("ERROR: Failed to Define the dom: %s" % test_dom)
        return status

    inst_list = {} 

    rc, cs = get_cs_instance(test_dom, server, virt)
    if rc != 0:
        cs = libvirt_cached_data_poll(server, virt, test_dom)
        if sys is None:
            logger.error("Instance for %s not created" % test_dom)
            cxml.undefine(server)
            return FAIL 

    inst_list[cs.CreationClassName] = cs.Name    

    try:
        status, host_inst = get_host_info(server, virt)
        if status != PASS:
            logger.error("Unable to get host information")
            cxml.undefine(server)
            return status


    except Exception, details:
        logger.error("DEBUG Exception: %s" % details)
        cxml.undefine(server)
        return FAIL 

    inst_list[host_inst.CreationClassName] = host_inst.Name

    prev_namespace = Globals.CIM_NS
    Globals.CIM_NS = 'root/interop'

    try:
        cn = get_typed_class(virt, 'RegisteredProfile')
        proflist = enumclass.EnumInstances(server, cn)
    except Exception, details:
        logger.error(CIM_ERROR_ENUMERATE, cn) 
        logger.error("Exception: %s", details)
        cxml.undefine(server)
        return status

    Globals.CIM_NS = prev_namespace

    exp_list = build_exp_prof_list(proflist, virt)

    # Loop through the assoc results returned on test_dom and hostsystem 
    try:
        for cn, sys_name in inst_list.iteritems():  
            name = sys_name
            an = get_typed_class(virt, "ElementConformsToProfile")
            profs = assoc.Associators(server,
                                      an,
                                      cn,
                                      CreationClassName=cn,
                                      Name=name)
            if len(profs) != 1:
                if cn == 'Linux_ComputerSystem':
                    status = XFAIL_RC(bug_sblim)
                else:   
                    logger.error("ElementConformsToProfile assoc failed")
                    status = FAIL

            if status != PASS:
                cxml.undefine(server)
                return status

            status = verify_profile(profs[0], exp_list[cn])
            if status != PASS:
                logger.error("Verification of profile instance failed")
                cxml.undefine(server)
                return FAIL

    except Exception, detail:
        logger.error(CIM_ERROR_ASSOCIATORS, an)
        logger.error("Exception: %s", detail)
        status = FAIL

    cxml.undefine(server)
    return status

if __name__ == "__main__":
    sys.exit(main())

