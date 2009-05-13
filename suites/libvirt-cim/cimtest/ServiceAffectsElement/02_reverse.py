#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
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
# This test case is used to verify the SAE association with the ComputerSystem, 
# Poiniting Device, DisplayController providers.
# The SAE association when queried with the ComputerSystem/PoinitingDevice/ 
# DisplayController should give the details of the CRS information
# to which they are part of.
#
# Ex: Command and some of the fields that are verified are given below.
# Command:

# wbemcli ain -ac KVM_ServiceAffectsElement 'http://root:passwd
# @localhost/root/virt:KVM_ComputerSystem.CreationClassName=\
# "KVM_ComputerSystem",Name="demo3"'
# 
# Output:
# -------
# host/root/virt:KVM_ConsoleRedirectionService.CreationClassName=\
# "KVM_ConsoleRedirectionService",Name="ConsoleRedirectionService",\
# SystemCreationClassName="KVM_HostSystem",SystemName="host"
# 
# Similarly the above o/p is expected when SAE is queired with 
# PoinitingDevice and DisplayController
#                                                         Date : 12-05-2009


import sys
from sets import Set
from XenKvmLib.assoc import Associators, compare_all_prop
from XenKvmLib import vxml
from CimTest.Globals import logger
from XenKvmLib.classes import get_typed_class
from XenKvmLib.enumclass import EnumInstances, EnumNames
from XenKvmLib.common_util import parse_instance_id
from XenKvmLib.const import do_main, get_provider_version
from CimTest.ReturnCodes import FAIL, PASS
from pywbem.cim_obj import CIMInstance

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
pd_dev_rev = 746
dc_dev_rev = 725

test_dom    = "SAE_dom"

def get_dom_records(cn, ei_info):
    ei_insts = {}
    for ei_item in ei_info:
        rec = None
        CCN = ei_item['CreationClassName']
        if 'DisplayController' in CCN or 'PointingDevice' in CCN : 
            guest, dev, status = parse_instance_id(ei_item['DeviceID'])
            if status != PASS:
                logger.error("Unable to parse DeviceID")
                return ei_insts, status

            if guest == test_dom:
                rec = ei_item
        elif 'ComputerSystem' in CCN:
            if ei_item['Name'] == test_dom:
                rec = ei_item
        else:
            logger.error("Unexpected CreationClassName %s returned by " \
                         "%s association", CCN, cn)
            return ei_insts, FAIL

        if not CCN in ei_insts.keys() and rec != None:
            ei_insts[CCN]=rec
        elif rec != None and (CCN in ei_insts.keys()):
            logger.error("Got more than one record for '%s'", CCN)
            return ei_insts, FAIL

    return ei_insts, PASS


def init_list_for_assoc(server, virt):
    c_list = [ 'ComputerSystem']
    curr_cim_rev, changeset = get_provider_version(virt, server)
    if curr_cim_rev >= pd_dev_rev:
        c_list.append('PointingDevice' )
    if curr_cim_rev >= dc_dev_rev:
        c_list.append('DisplayController')

    key_dict = {}
    for name in c_list:
        init_list = {} 
        c_name = get_typed_class(virt, name)
        ei_details = EnumNames(server, c_name)
        init_list, status = get_dom_records(c_name, ei_details)
        if status != PASS:
            return init_list, FAIL
        key_dict[c_name] = dict(init_list[c_name].keybindings)

    return key_dict, PASS

    
@do_main(sup_types)
def main():
    options = main.options
    server = options.ip
    virt = options.virt
    status = FAIL
    
    virt_xml = vxml.get_class(virt)
    cxml = virt_xml(test_dom)
    ret = cxml.cim_define(server)
    if not ret:
        logger.error("Failed to define the dom: %s", test_dom)
        return FAIL 

    an = get_typed_class(virt, "ServiceAffectsElement")
    
    try:
        in_list, status = init_list_for_assoc(server, virt)
        if status != PASS: 
            raise Exception("Failed to get init_list")

        c_name = get_typed_class(virt, 'ConsoleredirectionService')
        crs = EnumInstances(server, c_name)
        if len(crs) != 1:
            raise Exception("'%s' returned %i records, expected 1" \
                            % (c_name, len(crs)))

        for cn, value in in_list.iteritems(): 
            logger.info("Verifying '%s' association with '%s'", an, cn)
            if 'ComputerSystem' in cn:
                assoc_info = Associators(server, an, cn, 
                                               CreationClassName=cn,
                                               Name=value['Name'])
            else:
                assoc_info = Associators(server, an, cn, 
                                               CreationClassName=cn,
                                               SystemName=value['SystemName'],
                                               DeviceID=value['DeviceID'],
                                               SystemCreationClassName=\
                                               value['SystemCreationClassName'])
            if len(assoc_info) != 1:
                raise Exception("Got '%s' records for '%s' association with " \
                                "'%s',expected 1" %(len(assoc_info), an, cn))
            status = compare_all_prop(assoc_info[0], crs[0])

    except  Exception, detail :
        logger.error("Exception : %s", detail)
        status = FAIL

    cxml.undefine(server)
    return status

if __name__ == "__main__":
    sys.exit(main())
