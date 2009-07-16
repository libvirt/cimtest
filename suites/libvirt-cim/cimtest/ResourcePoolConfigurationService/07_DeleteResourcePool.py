#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri<dkalaker@in.ibm.com> 
#    
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
# This test case should test the  DeleteResourcePool service 
# supplied by the RPCS provider. 
# The DeleteResourcePool is used to delete a resource pool. 
# DeleteResourcePool() details:
# Input 
# -----
# IN -- Pool -- CIM_ResourcePool REF -- The resource pool to delete 
# 
# Output
# ------
# OUT -- Job -- CIM_ConcreteJob REF -- Returned job if started
# OUT -- Error-- String -- Encoded error instance if the operation 
#                          failed and did not return a job.
#
# Exception details before Revision 841
# -----
# Error code: CIM_ERR_NOT_SUPPORTED 
#
# After revision 841, the service is implemented
# 
#                                                  -Date: 20.02.2008


import sys
import pywbem 
from XenKvmLib import rpcs_service
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS
from XenKvmLib.const import do_main, platform_sup, get_provider_version
from XenKvmLib.enumclass import EnumInstances, EnumNames
from XenKvmLib.classes import get_typed_class
from XenKvmLib.common_util import destroy_netpool
from XenKvmLib.pool import create_pool, verify_pool

cim_errno  = pywbem.CIM_ERR_NOT_SUPPORTED
cim_mname  = "DeleteResourcePool"
libvirt_cim_child_pool_rev = 841
test_pool = "nat_pool"

@do_main(platform_sup)
def main():
    status = FAIL
    options = main.options
    rpcs_conn = eval("rpcs_service." + get_typed_class(options.virt, \
                      "ResourcePoolConfigurationService"))(options.ip)
    curr_cim_rev, changeset = get_provider_version(options.virt, options.ip)
    if curr_cim_rev < libvirt_cim_child_pool_rev:
        try:
            rpcs_conn.DeleteResourcePool()
        except pywbem.CIMError, (err_no, desc):
            if err_no == cim_errno :
                logger.info("Got expected exception for '%s' service",
                            cim_mname)
                logger.info("Errno is '%s' ", err_no)
                logger.info("Error string is '%s'", desc)
                return PASS
            else:
                logger.error("Unexpected rc code %s and description %s\n",
                             err_no, desc)
                return FAIL
    elif curr_cim_rev >= libvirt_cim_child_pool_rev:
        pool_attr = {
                     "Address" : "192.168.0.8",
                     "Netmask" : "255.255.255.0",
                     "IPRangeStart" : "192.168.0.9",
                     "IPRangeEnd"   : "192.168.0.15",
                     "ForwardMode" : pywbem.cim_types.Uint16(1)
                    }

        status = create_pool(options.ip, options.virt, test_pool, pool_attr)
        if status != PASS:
            logger.error("Error in networkpool creation")
            return status 
        
        status = verify_pool(options.ip, options.virt,  
                              test_pool, pool_attr)

        if status != PASS:
            logger.error("Error in networkpool verification")
            destroy_netpool(options.ip, options.virt, test_pool)
            return status 

        np = get_typed_class(options.virt, 'NetworkPool')
        np_id = "NetworkPool/%s" % test_pool
        netpool = EnumNames(options.ip, np)
        for i in range(0, len(netpool)):
            ret_pool = netpool[i].keybindings['InstanceID']
            if ret_pool == np_id:
                pool_settings = netpool[i]
                break
        try:
            rpcs_conn.DeleteResourcePool(Pool = pool_settings)
            netpool = EnumInstances(options.ip, np)
            for i in range(0, len(netpool)):
                ret_pool = netpool[i].InstanceID
                if ret_pool == np_id:
                    raise Exception("Failed to delete %s" % test_pool)
            status = PASS
        except Exception, details:
            logger.error(details)

    return status

if __name__ == "__main__":
    sys.exit(main())
