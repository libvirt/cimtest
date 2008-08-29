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
from VirtLib import live 
from XenKvmLib.common_util import get_host_info
from XenKvmLib.assoc import Associators
from XenKvmLib.vxml import XenXML, KVMXML, get_class
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger, CIM_ERROR_ASSOCIATORNAMES
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.test_xml import testxml
from XenKvmLib.test_doms import destroy_and_undefine_all

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
test_dom = "domgst"
test_vcpus = 1

def setup_env(server, virt="Xen"):
    status = PASS
    destroy_and_undefine_all(server)
    if virt == 'LXC':
        vsxml = get_class(virt)(test_dom)
    else:
        vsxml = get_class(virt)(test_dom, vcpus=test_vcpus)

    ret = vsxml.define(server)
    if not ret:
        logger.error("Failed to define the dom: %s", test_dom)
        status = FAIL

    return status, vsxml

def print_err(err, detail, cn):
    logger.error(err % cn)
    logger.error("Exception: %s", detail)

def get_inst_from_list(cn, qcn, list, filter, exp_val):
    status = PASS
    ret = -1
    inst = None
 
    if len(list) < 1:
        logger.error("%s returned %i %s objects" % (qcn, len(list), cn))
        return FAIL, None

    for inst in list:
        if inst[filter['key']] == exp_val:
            ret = PASS
            break

    if ret != PASS:
        status = FAIL
        logger.error("%s with %s was not returned" % (cn, exp_val))

    return status, inst 

def get_hostsys(server, virt="Xen"):
    cn = '%s_HostSystem' % virt
    status = PASS 
    host = live.hostname(server)

    try:
        status, hostname, clsname = get_host_info(server, virt)
        if hostname != host:
            status = FAIL
            logger.error("Hostname mismatch %s : %s" % (cn, host))

    except Exception, detail:
        logger.error("Exception in %s : %s" % (cn, detail))
        status = FAIL 

    return status, hostname, clsname

def get_hostrespool(server, hostsys, clsname, virt="Xen"):
    ccn1 = '%s_HostSystem' % virt
    an1 = '%s_HostedResourcePool' % virt
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
                                 ccn1,
                                 virt,
                                 CreationClassName = clsname,
                                 Name = hostsys)
        if len(assoc_info) < 4:
            logger.error("HostedResourcePool has returned %i instances, expected 4 \
instances", len(assoc_info))
            status = FAIL
            return status, devpool

        for inst in assoc_info:
            for a, val in ccnlist.items():
                if inst['AllocationUnits'] == val:
                    if inst.classname == a:
                        devpool.append(inst)

    except Exception, detail:
        print_err(CIM_ERROR_ASSOCIATORNAMES, detail, ccn1)
        status = FAIL

    return status, devpool 

def get_alloccap(server, devpool, virt="Xen"):
    an = '%s_ElementCapabilities' % virt
    cn = '%s_AllocationCapabilities' % virt
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
                                 virt,
                                 InstanceID = inst['InstanceID'])

            if len(assoc_info) < 1:
                logger.error("ElementCapabilities has returned %i objects", len(assoc_info))
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
    ccn = '%s_AllocationCapabilities' % virt
    an = '%s_SettingsDefineCapabilities' % virt
   
    if virt == 'LXC':
        rtype = { "%s_MemResourceAllocationSettingData" % virt :  4 }
    else:
        rtype = {
                  "%s_DiskResourceAllocationSettingData" % virt : 17, \
                  "%s_MemResourceAllocationSettingData" % virt :  4, \
                  "%s_NetResourceAllocationSettingData" % virt : 10, \
                  "%s_ProcResourceAllocationSettingData" % virt :  3
                 }
    rangelist = {
                  "Default"   : 0, \
                  "Minimum"   : 1, \
                  "Maximum"   : 2, \
                  "Increment" : 3
                }

    try:
        for ap in alloccap:
            assoc_info = Associators(server,
                                     an,
                                     ccn,
                                     virt,
                                     InstanceID = ap['InstanceID'])

            if len(assoc_info) != 4:
                logger.error("SettingsDefineCapabilities returned %i ResourcePool \
objects instead of 4", len(assoc_info))
                return FAIL

            for inst in assoc_info:

                cn = inst.classname
                if cn in rtype:
                    status = check_rasd_vals(inst, cn, rtype[cn], rangelist)
                    if status != PASS:
                        return status

                else:
                    logger.error("Unexpected instance type %s" % cn)
                    return FAIL

    except Exception, detail:
        print_err(CIM_ERROR_ASSOCIATORNAMES, detail, ccn)
        status = FAIL

    return status 

def check_rasd_vals(inst, cn, rt, rangelist):
    try:
        if inst['ResourceType'] != rt:
            logger.error("In ResourceType for %s " % rt)
            return FAIL
 
    except Exception, detail:
        logger.error("Error checking RASD attribute values %s" % detail)
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

