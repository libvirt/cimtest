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
from VirtLib.live import virsh_version
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from CimTest.Globals import logger, CIM_ERROR_GETINSTANCE, CIM_ERROR_ASSOCIATORS
from XenKvmLib.const import do_main, default_pool_name, default_network_name
from XenKvmLib.classes import get_typed_class
from XenKvmLib.common_util import print_field_error

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
        instance = enumclass.getInstance(ip, pool_class, key_list, virt)
    except Exception, detail:
        logger.error(CIM_ERROR_GETINSTANCE, '%s' % pool_class)
        logger.error("Exception: %s", detail)
        sys.exit(FAIL)
    return instance 

def init_list(virt, pool):
    """
        Creating the lists that will be used for comparisons.
    """
    
    if virt == 'LXC':
        instlist = [ pool[1].InstanceID ]
        cllist = [ get_typed_class(virt, "MemResourceAllocationSettingData") ]
        rtype = { get_typed_class(virt, "MemResourceAllocationSettingData")  :  4 }
    else:    
        instlist = [ 
                    pool[0].InstanceID,
                    pool[1].InstanceID, 
                    pool[2].InstanceID, 
                    pool[3].InstanceID
                   ]
        cllist = [ 
                  get_typed_class(virt, "DiskResourceAllocationSettingData"),
                  get_typed_class(virt, "MemResourceAllocationSettingData"), 
                  get_typed_class(virt, "NetResourceAllocationSettingData"), 
                  get_typed_class(virt, "ProcResourceAllocationSettingData")
                 ]
        rtype = { 
                  get_typed_class(virt, "DiskResourceAllocationSettingData") : 17, 
                  get_typed_class(virt, "MemResourceAllocationSettingData")  :  4, 
                  get_typed_class(virt, "NetResourceAllocationSettingData")  : 10, 
                  get_typed_class(virt, "ProcResourceAllocationSettingData") :  3
                }
    rangelist = {
                  "Default"   : 0, 
                  "Minimum"   : 1, 
                  "Maximum"   : 2, 
                  "Increment" : 3 
                }
    return instlist, cllist, rtype, rangelist

def get_pool_info(virt, server, devid, poolname=""):
        pool_cname = get_typed_class(virt, poolname)
        pool_cn = eval("enumclass." + pool_cname)
        return get_or_bail(virt, server, id=devid, pool_class=pool_cn)

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

def verify_rasd_fields(loop, assoc_info, cllist, rtype, rangelist):
    for inst in assoc_info:
        if inst.classname != cllist[loop]:
            print_field_error("Classname", inst.classname, cllist[loop])
            return FAIL 
        if inst['ResourceType'] != rtype[cllist[loop]]:
            print_field_error("ResourceType", inst['ResourceType'], 
                              rtype[cllist[loop]])
            return FAIL 

    return PASS

def verify_sdc_with_ac(virt, server, pool):
    loop = 0 
    instlist, cllist, rtype, rangelist = init_list(virt, pool)
    assoc_cname = get_typed_class(virt, "SettingsDefineCapabilities")
    cn =  get_typed_class(virt, "AllocationCapabilities")
    for instid in sorted(instlist):
        try:
            assoc_info = assoc.Associators(server, assoc_cname, cn, 
                                           InstanceID = instid)  
            if len(assoc_info) != 4:
                logger.error("%s returned %i ResourcePool objects"
                             "instead 4", assoc_cname, len(assoc_info))
                status = FAIL
                break
            status = verify_rasd_fields(loop, assoc_info, cllist, rtype, 
                                        rangelist)
            if status != PASS:
                break
            else:
                loop = loop + 1 

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
