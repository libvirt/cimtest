#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
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
# Get the setting data properties for the given guest starting from the host 
#
#
# It traverses the following path: 
# {Hostsystem} --> [HostedDependency]
# ( from output select guest domain instance of ComputerSystem) 
# --> [SystemDevice](from output select guest domain instance of Device, 
# from the guest domain instances, select one Device instance) --> [SettingsDefineState]
# (Verify the Device RASD returned with the values expected - those given in test_xml)
#
# Steps:
# ------
# 1) Get the hostname by enumerating the hostsystem.
# 2) Create a guest domain.
# 3) Get the Domains by using the HostedDependency association by supplying 
#    the inputs obtained from querying the hostsystem.
# 4) Get the various devices allocated to the domain by using the SystemDevice
#    association and giving the ComputerSystem output from the previous HostedDependency 
#    as inputs. 
# 5) For each of the Devices get the association on SettingsDefineState.
# 6) Verify the Disk, Memory, Network, Processor RASD values.
# 7) Destroy the guest domain.
#                                                                      Date : 29.01.2008

import sys
from CimTest.Globals import do_main
from XenKvmLib.vxml import get_class
from XenKvmLib.classes import get_typed_class
from XenKvmLib.test_doms import destroy_and_undefine_all
from XenKvmLib.assoc import Associators, AssociatorNames
from XenKvmLib.common_util import get_host_info
from CimTest.Globals import logger, CIM_ERROR_ASSOCIATORNAMES, \
CIM_ERROR_ASSOCIATORS
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.rasd import verify_procrasd_values, verify_netrasd_values, \
verify_diskrasd_values, verify_memrasd_values, rasd_init_list

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']


test_dom    = "CrossClass_GuestDom"
test_vcpus  = 1
test_mem    = 128
test_mac    = "00:11:22:33:44:aa"

def setup_env(server, virt="Xen"):
    vsxml_info = None
    status = PASS
    destroy_and_undefine_all(server)
    global test_disk
    if virt == "Xen":
        test_disk = "xvda"
    else: 
        test_disk = "hda"
    virt_xml =  get_class(virt)
    if virt == 'LXC':
        vsxml_info = virt_xml(test_dom)
    else:
        vsxml_info = virt_xml(test_dom, mem = test_mem,
                              vcpus=test_vcpus,
                              mac = test_mac,
                              disk = test_disk)
    
    ret = vsxml_info.define(server)
    if not ret:
        logger.error("Failed to define the dom: %s", test_dom)
        status = FAIL

    return status, vsxml_info

def print_err(err, detail, cn):
    logger.error(err % cn)
    logger.error("Exception: %s", detail)

def get_inst_from_list(server, cn, cs_list, filter_name, exp_val, vsxml):
    status = PASS
    ret = -1
    inst = []
    for inst in cs_list:
        if inst[filter_name['key']] == exp_val:
            ret = PASS
            break

    if ret != PASS:
        logger.error("%s with %s was not returned" % (cn, exp_val))
        vsxml.undefine(server)
        status = FAIL

    return status, inst

def get_assoc_info(server, cn, an, qcn, name, vsxml, virt="Xen"):
    status = PASS
    assoc_info = []
    try:
        assoc_info = AssociatorNames(server,
                                     an,
                                     cn,
                                     virt,
                                     CreationClassName = cn,
                                     Name = name)
        if len(assoc_info) < 1:
            logger.error("%s returned %i %s objects" % (an, len(assoc_info), qcn))
            status = FAIL

    except Exception, detail:
        print_err(CIM_ERROR_ASSOCIATORNAMES, detail, cn)
        status = FAIL

    if status != PASS:
        vsxml.undefine(server)

    return status, assoc_info

def verify_RASD_values(server, sd_assoc_info, vsxml, virt="Xen"):
    in_setting_define_state = {} 
    status = PASS
    try:
        for i in range(len(sd_assoc_info)):
            if sd_assoc_info[i]['SystemName'] == test_dom:
                classname_keyvalue = sd_assoc_info[i]['CreationClassName']
                deviceid =  sd_assoc_info[i]['DeviceID']
                in_setting_define_state[classname_keyvalue] = deviceid

        status, rasd_values, in_list = rasd_init_list(vsxml, virt, 
                                                      test_disk, test_dom, 
                                                      test_mac, test_mem)
        if status != PASS:
            return status

        an = get_typed_class(virt, 'SettingsDefineState')
        sccn = get_typed_class(virt, 'ComputerSystem')
        for cn, devid in sorted(in_setting_define_state.items()):
            assoc_info = Associators(server,
                                     an,
                                     cn,
                                     virt,
                                     DeviceID = devid,
                                     CreationClassName = cn,
                                     SystemName = test_dom,
                                     SystemCreationClassName = sccn)

            if len(assoc_info) != 1:
                logger.error("%s returned %i %s objects" % (an, len(assoc_info), cn))
                status = FAIL
                break
            index = (len(assoc_info) - 1)
            rasd  = rasd_values[cn]
            CCName = assoc_info[index].classname
            if 'ProcResourceAllocationSettingData' in CCName:
                status = verify_procrasd_values(assoc_info[index], rasd)
            elif 'NetResourceAllocationSettingData' in CCName:
                status  = verify_netrasd_values(assoc_info[index], rasd)
            elif 'DiskResourceAllocationSettingData' in CCName:
                status = verify_diskrasd_values(assoc_info[index], rasd)
            elif 'MemResourceAllocationSettingData' in CCName:
                status  = verify_memrasd_values(assoc_info[index], rasd)
            else:
                status = FAIL
            if status != PASS:
                logger.error("Mistmatching association values" )
                break
    except Exception, detail:
        print_err(CIM_ERROR_ASSOCIATORS, detail, an)
        status = FAIL
    return status

@do_main(sup_types)
def main():
    options = main.options
    server = options.ip
    status = PASS
    status, host_name, classname = get_host_info(server, options.virt)
    if status != PASS:
        return status
    status, vsxml = setup_env(server, options.virt)
    if status != PASS or vsxml == None:
        return status
    cn   = classname
    an   = get_typed_class(options.virt, 'HostedDependency')
    qcn  = get_typed_class(options.virt, 'ComputerSystem')
    name = host_name
    status, cs_assoc_info = get_assoc_info(server, cn, an, qcn, name, vsxml, options.virt)
    if status != PASS or len(cs_assoc_info) == 0:
        return status
    filter_name =  {"key" : "Name"}
    status, cs_dom = get_inst_from_list(server,
                                           cn,
                                 cs_assoc_info,
                                   filter_name,
                                      test_dom,
                                         vsxml)
    if status != PASS or len(cs_dom) == 0:
        return status
    cn   = cs_dom['CreationClassName']
    an   = get_typed_class(options.virt, 'SystemDevice') 
    qcn  = 'Devices'
    name = test_dom
    status, sd_assoc_info = get_assoc_info(server, cn, an, qcn, name, vsxml, options.virt)
    if status != PASS or len(sd_assoc_info) == 0:
        return status
    status = verify_RASD_values(server, sd_assoc_info, vsxml, options.virt)
    vsxml.undefine(server)
    return status
if __name__ == "__main__":
    sys.exit(main())
