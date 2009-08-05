#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
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

# This tc is used to verify the ResourceType,
# PropertyPolicy,ValueRole,ValueRange prop 
# are appropriately set when verified using the 
# Xen_SettingsDefineCapabilities asscoiation.
#
# Example association command :
# wbemcli ai -ac Xen_SettingsDefineCapabilities 
# 'http://localhost:5988/root/virt:
# Xen_AllocationCapabilities.InstanceID="DiskPool/foo"'
# 
# Output:
# ....
# localhost:5988/root/virt:
# Xen_DiskResourceAllocationSettingData.InstanceID="Maximum"
# -InstanceID="Maximum"
# -ResourceType=17
# -PropertyPolicy=0 (This is either 0 or 1)
# -ValueRole=3      ( greater than 0 and less than 4)
# -ValueRange=2     
# ( ValueRange is
#   0 - Default
#   1 - Minimum
#   2 - Maximum
#   3 - Increment 
# )
# .....
# 
# Similarly we check for Memory,Network,Processor.
#
#                                                Date : 21-12-2007

import sys
import os
from distutils.file_util import move_file
from XenKvmLib import assoc
from XenKvmLib import enumclass
from XenKvmLib.xm_virt_util import virsh_version
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from CimTest.Globals import logger, CIM_ERROR_GETINSTANCE, \
                            CIM_ERROR_ASSOCIATORS
from XenKvmLib.const import do_main, default_pool_name, default_network_name, \
                            get_provider_version
from XenKvmLib.classes import get_typed_class
from XenKvmLib.rasd import get_exp_template_rasd_len, dasd_cn, masd_cn, \
                           nasd_cn, pasd_cn, svrasd_cn, \
                           libvirt_rasd_storagepool_changes
from XenKvmLib.vsms import RASD_TYPE_DISK,  RASD_TYPE_MEM,  RASD_TYPE_PROC, \
                           RASD_TYPE_NET_ETHER,  RASD_TYPE_STOREVOL

platform_sup = ['Xen', 'KVM', 'XenFV', 'LXC']

memid = "MemoryPool/0"
procid = "ProcessorPool/0"
netid = "NetworkPool/%s" % default_network_name 
diskid = "DiskPool/%s" % default_pool_name

def get_or_bail(virt, ip, id, pool_class):
    """
        Getinstance for the Class and return instance on success, otherwise
        exit after cleanup_restore .
    """
    key_list = { 'InstanceID' : id } 
    try:
        instance = enumclass.GetInstance(ip, pool_class, key_list)
    except Exception, detail:
        logger.error(CIM_ERROR_GETINSTANCE, '%s', pool_class)
        logger.error("Exception: %s", detail)
        sys.exit(FAIL)
    return instance 

def init_list(virt, server, pool):
    """
        Creating the lists that will be used for comparisons.
    """
    
    memrasd = get_typed_class(virt, masd_cn)

    rtype = { memrasd  :  RASD_TYPE_MEM }
 
    if virt == 'LXC':
        instlist = [ pool[1].InstanceID ]
    else:    
        instlist = [ 
                    pool[0].InstanceID,
                    pool[1].InstanceID, 
                    pool[2].InstanceID, 
                    pool[3].InstanceID
                   ]

        rtype[get_typed_class(virt, dasd_cn)] = RASD_TYPE_DISK
        rtype[get_typed_class(virt, nasd_cn)] = RASD_TYPE_NET_ETHER
        rtype[get_typed_class(virt, pasd_cn)] = RASD_TYPE_PROC

        curr_cim_rev, changeset = get_provider_version(virt, server)
        if curr_cim_rev >= libvirt_rasd_storagepool_changes:
            rtype[get_typed_class(virt, svrasd_cn)] = RASD_TYPE_STOREVOL

    rangelist = {
                  "Default"   : 0, 
                  "Minimum"   : 1, 
                  "Maximum"   : 2, 
                  "Increment" : 3 
                }
    return instlist, rtype, rangelist

def get_pool_info(virt, server, devid, poolname=""):
        pool_cname = get_typed_class(virt, poolname)
        return get_or_bail(virt, server, id=devid, pool_class=pool_cname)

def get_pool_details(virt, server):  
    dpool = npool  = mpool  = ppool = None
    pool_set = []
    try :
        dpool = get_pool_info(virt, server, diskid, poolname="DiskPool") 
        mpool = get_pool_info(virt, server, memid, poolname= "MemoryPool")
        ppool = get_pool_info(virt, server, procid, poolname= "ProcessorPool")

        npool = get_pool_info(virt, server, netid, poolname= "NetworkPool")
        if dpool.InstanceID == None or mpool.InstanceID == None \
           or npool.InstanceID == None or ppool.InstanceID == None:
           logger.error("Get pool None") 
           return FAIL
        else:
           pool_set = [dpool, mpool, ppool, npool]      
    except Exception, detail:
        logger.error("Exception: %s", detail)
        return FAIL, pool_set

    return PASS, pool_set

def verify_rasd_fields(assoc_info, rtype, rangelist):
    for inst in assoc_info:
        if not inst.classname in rtype.keys():
            logger.error("Classname Mismatch, '%s' not in '%s'", 
                          inst.classname, rtype.keys())
            return FAIL 
        if inst['ResourceType'] != rtype[inst.classname]:
            logger.error("ResourceType Mismatch, got '%s' expected '%s'", 
                          inst['ResourceType'], rtype[inst.classname])
            return FAIL 

    return PASS

def verify_sdc_with_ac(virt, server, pool):
    instlist, rtype, rangelist = init_list(virt, server, pool)
    assoc_cname = get_typed_class(virt, "SettingsDefineCapabilities")
    cn =  get_typed_class(virt, "AllocationCapabilities")
    for instid in sorted(instlist):
        try:
            assoc_info = assoc.Associators(server, assoc_cname, cn, 
                                           InstanceID = instid)  

            exp_len = get_exp_template_rasd_len(virt, server, instid)

            if len(assoc_info) != exp_len:
                logger.error("%s returned %i ResourcePool objects instead"
                             " of %i", assoc_cname, len(assoc_info), exp_len)
                status = FAIL
                break
            status = verify_rasd_fields(assoc_info, rtype, rangelist)
            if status != PASS:
                break

        except Exception, detail:
            logger.error(CIM_ERROR_ASSOCIATORS, assoc_cname)
            logger.error("Exception: %s", detail)
            status = FAIL

    return status

@do_main(platform_sup)
def main():
    options = main.options

    server = options.ip
    virt = options.virt

    status, pool = get_pool_details(virt, server)
    if status != PASS:
        return FAIL

    status = verify_sdc_with_ac(virt, server, pool)

    return status
    
if __name__ == "__main__":
    sys.exit(main())
