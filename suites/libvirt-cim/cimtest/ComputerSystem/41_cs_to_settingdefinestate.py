#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
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

#
# This is a cross-provider testcase to 
# Verify starting ComputerSystem instance is the same as returned by the 
# SettingsDefineState.
#
# It traverses the following path: 
# {ComputerSystem} (select the guest domain) --> [SystemDevice](from output 
# select guest domain instances of Device, from the guest domain instances, 
# select one Device instance) --> [SettingsDefineState] (from output, select 
# a RASD instance - should only be 1) --> [VSSDComponent] (from output, 
# select a VSSD instance - should only be 1) --> [SettingsDefineState] 
# (Verify the ComputerSystem instance is the one we started with)
#
# Steps:
# ------
# 1) Create a guest domain.  
# 2) Enumerate ComputerSystem and Select the guest domain from the output 
#    and and verify the EnabledState is 2.
# 3) Create info list for the guest domain to be used later for comparison.
# 4) Get the various devices allocated to the domain by using the SystemDevice
#    association and giving the ComputerSystem output from the previous 
#    enumeration as inputs to the association. 
# 5) For each of the Devices get the association on SettingsDefineState, we 
#    should get only one record as output.
# 6) Verify the Disk, Memory, Network, Processor RASD values.
# 7) Call VSSDComponent association for each of the RASD types, we should
#    get only one VSSD record as output.  
# 8) Verify the VSSD output for every VSSDComponent association with the 
#    RASD types.
# 9) Using the VSSD output query the SettingsDefineState association, again we 
#    should get only one computersystem record as output.
# 10)Verify the computersystem values with the computersystem info that was 
#    created from the enumeration in the beginning.
# 11) Destroy the domain.
#                                                           Date : 05.02.2008

import sys
from XenKvmLib.vxml import get_class
from XenKvmLib.classes import get_typed_class
from XenKvmLib.assoc import Associators, AssociatorNames, compare_all_prop
from CimTest.Globals import logger, CIM_ERROR_ASSOCIATORS
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.rasd import enum_rasds
from XenKvmLib.enumclass import GetInstance
from XenKvmLib.common_util import parse_instance_id

sup_types = ['Xen', 'XenFV', 'KVM']

test_dom    = "CrossClass_GuestDom"

def setup_env(server, virt):
    vsxml_info = None
    virt_xml =  get_class(virt)

    vsxml_info = virt_xml(test_dom)
    ret = vsxml_info.cim_define(server)
    if not ret:
        logger.error("Failed to define the dom: %s", test_dom)
        return FAIL, vsxml_info

    status = vsxml_info.cim_start(server)
    if not ret:
        logger.error("Failed to start the dom: %s", test_dom)
        vsxml_info.undefine(server)
        return FAIL, vsxml_info

    return PASS, vsxml_info

def get_associators_info(server, cn, an, qcn, instid):
    status = PASS
    assoc_info = []
    try:
        assoc_info = Associators(server,
                                 an,
                                 cn,
                                 InstanceID = instid)
        if len(assoc_info) < 1:
            logger.error("%s returned %i %s objects", 
                         an, len(assoc_info), qcn)
            status = FAIL

    except Exception, detail:
        logger.error(CIM_ERROR_ASSOCIATORS, cn)
        logger.error("Exception: %s", detail)
        status = FAIL

    return status, assoc_info

def init_rasd_list(virt, ip):
    rasd_insts = {}
    rasds, status = enum_rasds(virt, ip)
    if status != PASS:
        logger.error("Enum RASDs failed")
        return rasd_insts, status

    for rasd_cn, rasd_list in rasds.iteritems():
        for rasd in rasd_list:
            guest, dev, status = parse_instance_id(rasd.InstanceID)
            if status != PASS:
                logger.error("Unable to parse InstanceID: %s", rasd.InstanceID)
                return rasd_insts, FAIL

            if guest == test_dom:
                rasd_insts[rasd.Classname] = rasd

    return rasd_insts, PASS


def verify_values(assoc_info, vssd_cs_values, an, qcn):
    if len(assoc_info) != 1:
        logger.error("%s returned %i %s objects, Expected 1", an,
                     len(assoc_info), qcn)
        return FAIL

    vssd_cs_assoc = assoc_info[0]
    return compare_all_prop(vssd_cs_assoc, vssd_cs_values)

def build_sd_info(sd_assoc_info, qcn, an, rasd_values):
    sd_info = {} 

    # Building the input for SettingsDefineState association.
    for sd_val in sd_assoc_info:
        if sd_val['SystemName'] == test_dom:
            classname_keyvalue = sd_val['CreationClassName']
            deviceid =  sd_val['DeviceID']
            sd_info[classname_keyvalue] = deviceid

    # Expect the SystemDevice records == len(rasd_values) entries.
    if len(sd_info) != len(rasd_values):
        logger.error("%s returned %i %s objects, Expected %i", an,
                     len(sd_info), qcn, len(rasd_values))
        return FAIL, sd_info

    return PASS, sd_info

def get_cs_sysdev_info(server, virt, qcn, rasd_val):
    sd_info={}
    try: 
        cs_class = get_typed_class(virt, 'ComputerSystem')
        keys = { 'Name' : test_dom, 'CreationClassName' : cs_class }
        dom_cs = GetInstance(server, cs_class, keys)
        if dom_cs.Name != test_dom:
            raise Exception("Instance matching %s was not returned" % test_dom)

        an = get_typed_class(virt, 'SystemDevice')
        sd_assoc = AssociatorNames(server, an, cs_class,
                                   CreationClassName=cs_class, 
                                   Name=test_dom)
        if len(sd_assoc) < 1:
            raise Exception("%s returned %d %s objects"  \
                            % (an, len(sd_assoc), qcn))

        status, sd_info = build_sd_info(sd_assoc, qcn, an, rasd_val)        
        if status != PASS:
            raise Exception("Failed to get SystemDevice info for: %s" \
                            % test_dom)

    except Exception, details:
        logger.error("Exception details: %s", details)
        return FAIL, dom_cs, sd_info

    return PASS, dom_cs, sd_info

def get_sds_info(server, virt, cs_cn, rasd_values,
                 in_setting_define_state, qcn):
    sds_info = {}
    try:

        an = get_typed_class(virt,"SettingsDefineState")
        for cn, devid in sorted(in_setting_define_state.items()):
            assoc_info = Associators(server, an, cn, DeviceID = devid,
                                     CreationClassName = cn,
                                     SystemName = test_dom,
                                     SystemCreationClassName = cs_cn)

            # we expect only one RASD record to be returned for each device 
            # type when queried with SDS association.
            if len(assoc_info) != 1:
                raise Exception("%s returned %d %s objects, Expected 1" \
                                % (an, len(assoc_info), cn))
            
            assoc_val = assoc_info[0]
            CCName = assoc_val.classname
            exp_rasd = rasd_values[CCName]
            if assoc_val['InstanceID'] != exp_rasd.InstanceID:
                raise Exception("Got %s instead of %s" \
                                 % (assoc_val['InstanceID'], 
                                    exp_rasd.InstanceID))

            # Build the input required for VSSDC association query.
            vs_name = assoc_val['InstanceID']
            if vs_name.find(test_dom) >= 0:
                instid =  assoc_val['InstanceID']
                sds_info[CCName] = instid 

        if len(sds_info) != len(rasd_values):
            raise Exception("%s returned %i %s objects, Expected %i" \
                            % (an, len(sds_info), qcn, len(rasd_values)))

    except Exception, details:
        logger.error("Exception: %s", details)
        return FAIL, sds_info

    return PASS, sds_info

def get_vssd_info(server, virt, in_vssdc_list, qcn): 
    try:
        # Get the vssd values which will be used for verifying the 
        # VSSD output from the VSSDC results.
        if virt == "XenFV":
            instIdval = "Xen:%s" % test_dom
        else:
            instIdval = "%s:%s" % (virt, test_dom)

        vssd_class = get_typed_class(virt, 'VirtualSystemSettingData')
        keys = { 'InstanceID' : instIdval }
        vssd_values = GetInstance(server, vssd_class, keys)
        if vssd_values.ElementName != test_dom:
            raise Exception("Instance matching %s was not returned"  % test_dom)

        an = get_typed_class(virt, 'VirtualSystemSettingDataComponent')
        for cn, instid in sorted((in_vssdc_list.items())):
            status, vssd_assoc_info = get_associators_info(server, cn, an, 
                                                           vssd_class, 
                                                           instid)
            if status != PASS:
                raise Exception("Failed to get VSSD info")

            status = verify_values(vssd_assoc_info, vssd_values, an, qcn)    
            if status != PASS:
                raise Exception("VSSD values verification error")

    except Exception, details:
        logger.error("Exception details: %s", details)
        return FAIL, vssd_assoc_info 

    return PASS, vssd_assoc_info 

def verify_vssdc_assoc(server, virt, cs_class, vssd_assoc_info, dom_cs): 
    try:
        # Since the VirtualSystemSettingDataComponent returns similar 
        # output when queried with every RASD, we are taking the output of 
        # the last associtaion query as inputs for 
        # querying SettingsDefineState.
        cn = vssd_assoc_info[0].classname
        an = get_typed_class(virt, 'SettingsDefineState')
        instid = vssd_assoc_info[0]['InstanceID']
        status, cs_assoc_info = get_associators_info(server, cn, an, 
                                                     cs_class, instid)
        if status != PASS:
            raise Exception("Failed to get assoc info for dom: %s" % test_dom)

        # verify the results of SettingsDefineState with the cs_values list 
        # that was built using the output of the GetInstance on ComputerSystem.
        status = verify_values(cs_assoc_info, dom_cs, an, cs_class)

    except Exception, details:
        logger.error("Exception details: %s", details)
        return FAIL

    return status
         

@do_main(sup_types)
def main():
    server = main.options.ip
    virt   = main.options.virt

    try:
        status, vsxml = setup_env(server, virt)
        if status != PASS:
            return status

        qcn = 'Logical Devices'
        rasd_val, status = init_rasd_list(virt, server)

        status, dom_cs, sd_info = get_cs_sysdev_info(server, virt, 
                                                      qcn, rasd_val)
        if status != PASS:
            raise Exception("Failed to get SystemDevice information")

        cs_class = dom_cs.CreationClassName

        status, sds_info = get_sds_info(server, virt, cs_class, rasd_val, 
                                        sd_info, qcn)
        if status != PASS:
            raise Exception("Failed to get SetingDefineState information")

        status, vssd_assoc_info = get_vssd_info(server, virt, sds_info, qcn)
        if status != PASS:
            raise Exception("Failed to get VSSD information")

        status = verify_vssdc_assoc(server, virt, cs_class,
                                    vssd_assoc_info, dom_cs)

    except Exception, details:
        logger.error("Exception details is %s", details)
        status = FAIL

    vsxml.cim_destroy(server)
    vsxml.undefine(server)
    return status
if __name__ == "__main__":
    sys.exit(main())
