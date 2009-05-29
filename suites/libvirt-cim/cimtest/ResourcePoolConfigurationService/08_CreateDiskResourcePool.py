#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
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
# This test case should test the  CreateChildResourcePool service 
# supplied by the RPCS provider. 
# Input 
# -----
# IN -- ElementName -- String -- The desired name of the resource pool
# IN -- Settings    -- String -- A string representation of a
#                                CIM_ResourceAllocationSettingData 
#                                instance that represents the allocation 
#                                assigned to this child pool
# IN -- ParentPool  -- CIM_ResourcePool REF -- The parent pool from which 
#                                              to create this pool
# 
# Output
# ------
# OUT -- Pool -- CIM_ResourcePool REF -- The resulting resource pool
# OUT -- Job  -- CIM_ConcreteJob REF -- Returned job if started
# OUT -- Error -- String  -- Encoded error instance if the operation 
#                            failed and did not return a job
#
# Exception details before Revision 846
# -----
# Error code: CIM_ERR_NOT_SUPPORTED 
#
# After revision 846, the service is implemented
#
#                                                   -Date: 26.05.2009

import sys
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS
from XenKvmLib.const import do_main, platform_sup
from XenKvmLib.classes import get_typed_class
from XenKvmLib.common_util import destroy_diskpool
from XenKvmLib.pool import create_pool, verify_pool, undefine_diskpool

test_pool = "diskpool"
dp_types =  { "DISK_POOL_DIR" : 1 }
               

@do_main(platform_sup)
def main():
    options = main.options
    server = options.ip
    virt = options.virt
    pool_attr = { "Path" : "/tmp" }

    # For now the test case support only the creation of 
    # dir type disk pool, later change to fs and netfs etc 
    for key, value in dp_types.iteritems():    
        status = create_pool(server, virt, test_pool, pool_attr, 
                             mode_type=value, pool_type= "DiskPool")
        if status != PASS:
            logger.error("Failed to create '%s' type diskpool '%s'", 
                          key, test_pool)
            return FAIL

        status = verify_pool(server, virt, test_pool, pool_attr, 
                             mode_type=value, pool_type="DiskPool")
        if status != PASS:
            logger.error("Error in diskpool verification")
            destroy_diskpool(server, virt, test_pool)
            undefine_diskpool(server, virt, test_pool)
            return FAIL

        status = destroy_diskpool(server, virt, test_pool)
        if status != PASS:
            logger.error("Unable to destroy diskpool '%s'", test_pool)
            return FAIL

        status = undefine_diskpool(server, virt, test_pool)
        if status != PASS:
            logger.error("Unable to undefine diskpool '%s'", test_pool)
            return FAIL

        status = PASS
 
    return status

if __name__ == "__main__":
    sys.exit(main())
