#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com> 
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
# The test case verifies DeleteResourcePool is able to delete the 
# dir type diskpool.
#                                                  -Date: 26.05.2009

import sys
import pywbem
from XenKvmLib import rpcs_service
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS
from XenKvmLib.const import do_main, platform_sup, get_provider_version
from XenKvmLib.enumclass import EnumInstances, EnumNames
from XenKvmLib.classes import get_typed_class
from XenKvmLib.pool import create_pool, verify_pool, undefine_diskpool
from XenKvmLib.common_util import destroy_diskpool

cim_errno  = pywbem.CIM_ERR_NOT_SUPPORTED
cim_mname  = "DeleteResourcePool"
libvirt_cim_child_pool_rev = 841
test_pool = "dp_pool"
TYPE = 1 # Dir type diskpool

@do_main(platform_sup)
def main():
    status = FAIL
    options = main.options
    server = options.ip
    virt = options.virt 
    cn = get_typed_class(virt, "ResourcePoolConfigurationService")
    rpcs_conn = eval("rpcs_service." + cn)(server)
    curr_cim_rev, changeset = get_provider_version(virt, server)
    if curr_cim_rev < libvirt_cim_child_pool_rev:

        try:
            rpcs_conn.DeleteResourcePool()
        except pywbem.CIMError, (err_no, desc):
            if err_no == cim_errno :
                logger.info("Got expected exception for '%s' service", cim_mname)
                logger.info("Errno is '%s' ", err_no)
                logger.info("Error string is '%s'", desc)
                return PASS
            else:
                logger.error("Unexpected rc code %s and description %s\n",
                             err_no, desc)
                return status

    elif curr_cim_rev >= libvirt_cim_child_pool_rev:
        
        try:
            pool_attr = { "Path" : "/tmp" }
            status = create_pool(server, virt, test_pool, pool_attr, 
                                 pool_type="DiskPool", mode_type=TYPE)
            if status != PASS:
                logger.error("Failed to create diskpool '%s'", test_pool)
                return status 

            status = verify_pool(server, virt, test_pool, 
                                 pool_attr, pool_type="DiskPool")
            if status != PASS:
                raise Exception("Failed to verify diskpool '%s'" % test_pool)

            dp = get_typed_class(virt, 'DiskPool')
            dp_id = "DiskPool/%s" % test_pool
            pool_settings = None 
            pool = EnumNames(server, dp)
            for i in range(0, len(pool)):
                ret_pool = pool[i].keybindings['InstanceID']
                if ret_pool == dp_id:
                    pool_settings = pool[i]
                    break

            if pool_settings == None:
                logger.error("Failed to get poolsettings for '%s'", test_pool)
                return FAIL

            rpcs_conn.DeleteResourcePool(Pool = pool_settings)
            pool = EnumInstances(server, dp)
            for i in range(0, len(pool)):
                ret_pool = pool[i].InstanceID
                if ret_pool == dp_id:
                    raise Exception("Failed to delete diskpool '%s'" %test_pool)

            status = PASS
        except Exception, details:
            logger.error("Exception details: %s", details)
            destroy_diskpool(server, virt, test_pool)
            undefine_diskpool(server, virt, test_pool)
            return FAIL

    return status

if __name__ == "__main__":
    sys.exit(main())
