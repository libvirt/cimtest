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
# Exception details before Revision 837
# -----
# Error code: CIM_ERR_NOT_SUPPORTED 
#
# After revision 837, the service is implemented
#
#                                                   -Date: 20.02.2008

import sys
import random
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS
from XenKvmLib.const import do_main, platform_sup
from XenKvmLib.classes import get_typed_class
from XenKvmLib.common_util import destroy_netpool
from XenKvmLib.pool import create_netpool, verify_pool, undefine_netpool

test_pool = "testpool"

@do_main(platform_sup)
def main():
    options = main.options

    np = get_typed_class(options.virt, 'NetworkPool')
    np_id = "NetworkPool/%s" % test_pool

    subnet = '192.168.0.'
    ip_base = random.randint(1, 100)
    addr = subnet+'%d' % ip_base
    range_addr_start = subnet+'%d' % (ip_base + 1)
    range_addr_end = subnet+'%d' %(ip_base + 10)
    pool_attr = {
                 "Address" : addr,
                 "Netmask" : "255.255.255.0",
                 "IPRangeStart" : range_addr_start,
                 "IPRangeEnd"   : range_addr_end
                }
    for item in range(0, 3):    
        status = create_netpool(options.ip, options.virt, 
                                test_pool, pool_attr, mode_type=item)
        if status != PASS:
            logger.error("Error in networkpool creation")
            return FAIL

        status = verify_pool(options.ip, options.virt, np,
                             test_pool, pool_attr, mode_type=item)
        if status != PASS:
            logger.error("Error in networkpool verification")
            destroy_netpool(options.ip, options.virt, test_pool)
            undefine_netpool(options.ip, options.virt, test_pool)
            return FAIL

        status = destroy_netpool(options.ip, options.virt, test_pool)
        if status != PASS:
            logger.error("Unable to destroy networkpool %s", test_pool)
            return FAIL

        status = undefine_netpool(options.ip, options.virt, test_pool)
        if status != PASS:
            logger.error("Unable to undefine networkpool %s", test_pool)
            return FAIL

        status = PASS
 
    return status

if __name__ == "__main__":
    sys.exit(main())
