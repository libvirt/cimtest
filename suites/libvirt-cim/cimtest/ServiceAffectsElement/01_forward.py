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
# This test case is used to verify the SAE association with the CRS providers.
# The SAE association when queried with the CRS should give the details of the 
# Source from which the 
# 1) Console Flow can be started represented by the ComputerSystem class
# 2) Original Poiniting Device associated with the guest
# 3) Original Graphics Device associated with the guest
#
# Ex: Command and some of the fields that are verified are given below.
# Command
# -------
# wbemcli ain -ac KVM_ServiceAffectsElement 'http://root:passwd@localhost
# /root/virt:KVM_ConsoleRedirectionService.CreationClassName=\
# "KVM_ConsoleRedirectionService", Name="ConsoleRedirectionService",
# SystemCreationClassName="KVM_HostSystem",SystemName="host"'
# 
# Output 
# ------
# host/root/virt:KVM_ComputerSystem.CreationClassName="KVM_ComputerSystem",
# Name="demo2"
# host/root/virt:KVM_PointingDevice.CreationClassName="KVM_PointingDevice",
# DeviceID="demo2/mouse:ps2", SystemCreationClassName="KVM_ComputerSystem",
# SystemName="demo2"
# host/root/virt:KVM_DisplayController.CreationClassName=\
# "KVM_DisplayController",DeviceID="demo2/graphics",
# SystemCreationClassName="KVM_ComputerSystem",SystemName="demo2"
#                                                             Date : 12-05-2009


import sys
from sets import Set
from XenKvmLib import assoc
from XenKvmLib import vxml
from CimTest.Globals import logger
from XenKvmLib.classes import get_typed_class
from XenKvmLib.enumclass import EnumInstances
from XenKvmLib.common_util import parse_instance_id
from XenKvmLib.const import do_main, get_provider_version
from CimTest.ReturnCodes import FAIL, PASS

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
sae_assoc_with_input_graphics_rev = 795

test_dom    = "SAE_dom"

def get_dom_records(an_cn, assoc_ei_info, assoc_ei_insts):
    
    for assoc_ei_item in assoc_ei_info:
        rec = None
        CCN = assoc_ei_item['CreationClassName']
        if 'DisplayController' in CCN or 'PointingDevice' in CCN : 
            guest, dev, status = parse_instance_id(assoc_ei_item['DeviceID'])
            if status != PASS:
                logger.error("Unable to parse DeviceID")
                return assoc_ei_insts, status

            if guest == test_dom:
                rec = assoc_ei_item
        elif 'ComputerSystem' in CCN:
            if assoc_ei_item['Name'] == test_dom:
                rec = assoc_ei_item
        else:
            logger.error("Unexpected CreationClassName %s returned by " \
                        "%s association", CCN, an_cn)
            return assoc_ei_insts, FAIL

        if not CCN in assoc_ei_insts.keys() and rec != None:
            assoc_ei_insts[CCN]=rec
        elif rec != None and (CCN in assoc_ei_insts.keys()):
            logger.error("Got more than one record for '%s'", CCN)
            return assoc_ei_insts, FAIL

    return assoc_ei_insts, PASS


def init_list_for_compare(server, virt):
    c_list = [ 'ComputerSystem']
    curr_cim_rev, changeset = get_provider_version(virt, server)
    if curr_cim_rev >= sae_assoc_with_input_graphics_rev:
        c_list.append('PointingDevice' )
        c_list.append('DisplayController')

    init_list = {} 
    for name in c_list:
        c_name = get_typed_class(virt, name)
        ei_details = EnumInstances(server, c_name, ret_cim_inst=True)
        init_list, status = get_dom_records(c_name, ei_details, init_list)
        if status != PASS:
            return init_list, FAIL

    return init_list, PASS

    
def verify_assoc(server, virt, an, assoc_info):
    assoc_insts = {}
    try:
        assoc_insts, status = get_dom_records(an, assoc_info, assoc_insts)
        if status != PASS or len(assoc_insts) < 1 :
            raise Exception("Failed to get insts for domain %s" % test_dom)

        in_list, status = init_list_for_compare(server, virt)
        if status != PASS or len(in_list) != 3:
            raise Exception("Failed to get init_list")

        in_list_keys = Set(in_list.keys())
        assoc_list_keys = Set(assoc_insts.keys())
        if len(in_list_keys & assoc_list_keys) < 1 :
            raise Exception("Mistmatching Class Names, expected %s, got %s" \
                            % (in_list_keys, assoc_list_keys))

        for cname, prop in in_list.iteritems():
            logger.info("Verifying Values for '%s'", cname)
            exp_vals = in_list[cname].items()
            res_vals = assoc_insts[cname].items()
            for i in range(0, len(prop)):
                if exp_vals[i][1] != res_vals[i][1]:
                    logger.error("'%s' val mismatch for '%s': " \
                                 "got '%s', expected '%s'", exp_vals[i][0], 
                                 cname, res_vals[i][1], exp_vals[i][1])
                    return FAIL

    except Exception, details:
        logger.error("Exception in fn verify_assoc()")
        logger.error("Exception details: %s", details)
        return FAIL
    return PASS

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
        cname = 'ConsoleRedirectionService'
        classname = get_typed_class(virt, cname)
        crs = EnumInstances(server, classname)

        if len(crs) != 1:
            raise Exception("'%s' returned %i records, expected 1" \
                            % (classname, len(crs)))

        crs_val = crs[0]
        crs_cname = crs_val.CreationClassName
        crs_sccn = crs_val.SystemCreationClassName
        assoc_info = assoc.Associators(server, an, crs_cname,
                                       CreationClassName=crs_cname, 
                                       Name=crs_val.Name, 
                                       SystemCreationClassName=crs_sccn,
                                       SystemName=crs_val.SystemName)
        status = verify_assoc(server, virt, an, assoc_info)
    except  Exception, detail :
        logger.error("Exception : %s", detail)
        status = FAIL

    cxml.undefine(server)
    return status

if __name__ == "__main__":
    sys.exit(main())
