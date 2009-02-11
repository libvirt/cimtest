#!/usr/bin/python

#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Veerendra Chandrappa <vechandr@in.ibm.com>
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

# This is a cross-provider testcase.  It traverses the following path: 

# { HostSystem } ---> [ HostedResourcePool ] ---> [ ElementCapabilities ] ---> \
# [ SettingsDefineCapabilities ] ---> { RASD } 

# Steps:
#  1. Create a guest.
#  2. Enumerate the HostSystem .
#  3. Using the HostedResourcePool association, get the HostSystem instances on the system
#  4. Using the ElementCapabilities association get the ProcessorPool, MemPool, DiskPool &
#     NetPool instances on the system.
#  5. Using the SettingsDefineCapabilities association on the AllocationCapabilities, get 
#     the (Default, Minimum, Maximum and Increment) instances for ProcRASD.
#  6. Similarly for the MemRASD, DiskRASD & NetRASD get the SettingDefineCap assocn and \
#     get the instances for (Def, Min, Max and Inc).
#
# Feb 13 2008

import sys
from VirtLib.live import full_hostname 
from XenKvmLib.common_util import get_host_info
from XenKvmLib.assoc import Associators
from XenKvmLib.vxml import XenXML, KVMXML, get_class
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger, CIM_ERROR_ASSOCIATORNAMES
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.test_xml import testxml
from XenKvmLib.test_doms import destroy_and_undefine_all
from XenKvmLib.const import get_provider_version

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
test_dom = "domgst_test"
test_vcpus = 1
libvirt_rasd_template_changes = 707
libvirt_rasd_new_changes = 805

def setup_env(server, virt="Xen"):
    status = PASS
    destroy_and_undefine_all(server)
    if virt == 'LXC':
        vsxml = get_class(virt)(test_dom)
    else:
        vsxml = get_class(virt)(test_dom, vcpus=test_vcpus)

    ret = vsxml.cim_define(server)
    if not ret:
        logger.error("Failed to define the dom: %s", test_dom)
        status = FAIL

    return status, vsxml

def print_err(err, detail, cn):
    logger.error(err, cn)
    logger.error("Exception: %s", detail)

def get_inst_from_list(cn, qcn, list, filter, exp_val):
    status = PASS
    ret = -1
    inst = None
 
    if len(list) < 1:
        logger.error("%s returned %i %s objects", qcn, len(list), cn)
        return FAIL, None

    for inst in list:
        if inst[filter['key']] == exp_val:
            ret = PASS
            break

    if ret != PASS:
        status = FAIL
        logger.error("%s with %s was not returned", cn, exp_val)

    return status, inst 

def get_hostsys(server, virt="Xen"):
    status = PASS 
    host = full_hostname(server)

    try:
        status, host_inst = get_host_info(server, virt)
        if host_inst.Name != host:
            status = FAIL
            logger.error("Hostname mismatch") 

    except Exception, detail:
        logger.error("Exception in %s : %s", cn, detail)
        status = FAIL 

    return status, host_inst.Name, host_inst.CreationClassName 

def get_hostrespool(server, hostsys, clsname, virt="Xen"):
    an1 = get_typed_class(virt, "HostedResourcePool")
    status = PASS
    devpool = []
    
    if virt == 'LXC':
        ccnlist = { '%s_MemoryPool' % virt : 'KiloBytes'}
    else: 
        ccnlist = { '%s_ProcessorPool' % virt : 'Processors',
                    '%s_MemoryPool' % virt : 'KiloBytes',
                    '%s_DiskPool' % virt : 'Megabytes' ,
                    '%s_NetworkPool' % virt : None }
    try:
        assoc_info = Associators(server,
                                 an1,
                                 clsname,
                                 CreationClassName = clsname,
                                 Name = hostsys)
        if len(assoc_info) < 4:
            logger.error("'%s' has returned %i instances, expected 4"
                         " instances", an1, len(assoc_info))
            return FAIL, devpool

        for inst in assoc_info:
            for a, val in ccnlist.items():
                if inst['AllocationUnits'] == val:
                    if inst.classname == a:
                        devpool.append(inst)

    except Exception, detail:
        print_err(CIM_ERROR_ASSOCIATORNAMES, detail, clsname)
        status = FAIL

    return status, devpool 

def get_alloccap(server, devpool, virt="Xen"):
    an = get_typed_class(virt, 'ElementCapabilities')
    cn =  get_typed_class(virt, 'AllocationCapabilities')
    status = FAIL
    alloccap = []
    filter =  {"key" : "ResourceType"}

    if virt == 'LXC':
        ccnlist = { '%s_MemoryPool' % virt : 4 }
    else:
        ccnlist = { '%s_ProcessorPool' % virt: 3,
                    '%s_MemoryPool' % virt : 4, 
                    '%s_DiskPool' % virt : 17 ,
                    '%s_NetworkPool' % virt : 10 }
   
    for inst in devpool:
        try:
            assoc_info = Associators(server,
                                     an,
                                     inst.classname,
                                     InstanceID = inst['InstanceID'])

            if len(assoc_info) < 1:
                logger.error("'%s' has returned %i objects", an, len(assoc_info))
                status = FAIL
                return status, alloccap

            for c , rt in ccnlist.items():
                if c != inst.classname:
                    continue
                status, setdefcap = get_inst_from_list(an,
                                                      c,
                                                      assoc_info,
                                                      filter,
                                                      rt )
                if status != FAIL:
                    alloccap.append(setdefcap) 

        except Exception, detail:
            print_err(CIM_ERROR_ASSOCIATORNAMES, detail, cn)
            status = FAIL

    return status, alloccap

def get_rasddetails(server, alloccap, virt="Xen"):

    status = PASS
    ccn = get_typed_class(virt, 'AllocationCapabilities')
    an = get_typed_class(virt, 'SettingsDefineCapabilities')
   
    if virt == 'LXC':
        rtype = { "%s_MemResourceAllocationSettingData" % virt :  4 }
    else:
        rtype = {
                  "%s_DiskResourceAllocationSettingData" % virt : 17, \
                  "%s_MemResourceAllocationSettingData" % virt :  4, \
                  "%s_NetResourceAllocationSettingData" % virt : 10, \
                  "%s_ProcResourceAllocationSettingData" % virt :  3
                 }
    try:
        for ap in alloccap:
            assoc_info = Associators(server,
                                     an,
                                     ccn,
                                     InstanceID = ap['InstanceID'])

            curr_cim_rev, changeset = get_provider_version(virt, server)
            exp_len = 4
            if 'DiskPool' in ap['InstanceID']:
                # For Diskpool, we have info 1 for each of Min, Max, 
                # default, Increment and 1 for each of PV and FV 
                # hence 4 * 2 = 8 records
                if virt == 'Xen':
                    if curr_cim_rev >= libvirt_rasd_template_changes and \
                       curr_cim_rev < libvirt_read_new_changes:
                        exp_len = 8
                    if curr_cim_rev >= libvirt_read_new_changes:
                        exp_len = 16
                if virt == 'KVM':
                    if curr_cim_rev >= libvirt_rasd_new_changes:
                        exp_len = 8

            if len(assoc_info) != exp_len:
                logger.error("'%s' returned %i RASD objects instead of %i", 
                             an, len(assoc_info), exp_len)
                return FAIL

            for inst in assoc_info:

                cn = inst.classname
                if cn in rtype:
                    status = check_rasd_vals(inst, rtype[cn])
                    if status != PASS:
                        return status
                else:
                    logger.error("Unexpected instance type %s", cn)
                    return FAIL

    except Exception, detail:
        print_err(CIM_ERROR_ASSOCIATORNAMES, detail, ccn)
        status = FAIL

    return status 

def check_rasd_vals(inst, rt):
    try:
        if inst['ResourceType'] != rt:
            logger.error("In ResourceType for %s ", rt)
            return FAIL
    except Exception, detail:
        logger.error("Error checking RASD attribute values %s", detail)
        return FAIL

    return PASS

@do_main(sup_types)
def main():
    options = main.options
    status = PASS 

    server = options.ip
    virt = options.virt

    if virt == 'XenFV':
        virt = 'Xen'

    status, vsxml = setup_env(server, virt)
    if status != PASS:
        return status

    status, hs, clsname = get_hostsys(server, virt)
    if status != PASS or hs == None:
        vsxml.undefine(server)
        return status

    status, devpool = get_hostrespool(server, hs, clsname, virt)
    if status != PASS or devpool == None:
        vsxml.undefine(server)
        return status

    status, alloccap = get_alloccap(server, devpool, virt)
    if status != PASS or alloccap == None:
        vsxml.undefine(server)
        return status

    status = get_rasddetails(server, alloccap, virt)

    vsxml.undefine(server)
    return status

if __name__ == "__main__":
    sys.exit(main())

