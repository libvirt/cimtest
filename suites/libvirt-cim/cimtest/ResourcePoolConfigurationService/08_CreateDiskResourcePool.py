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
from XenKvmLib.xm_virt_util import virsh_version
from CimTest.ReturnCodes import FAIL, PASS, SKIP
from XenKvmLib.const import do_main, platform_sup
from XenKvmLib.classes import get_typed_class
from XenKvmLib.common_util import destroy_diskpool, nfs_netfs_setup, \
                                  netfs_cleanup
from XenKvmLib.pool import create_pool, verify_pool, undefine_diskpool
from XenKvmLib.const import get_provider_version

libvirt_disk_pool_support=837
libvirt_netfs_pool_support=869
    
def get_pool_attr(server, pool_type, dp_types, rev):
    pool_attr = { "Path" : "/var/lib/libvirt/images" }

    if rev >= libvirt_netfs_pool_support and \
       pool_type == dp_types['DISK_POOL_NETFS']:
        status , host_addr, src_mnt_dir, dir_mnt_dir = nfs_netfs_setup(server)
        if status != PASS:
            logger.error("Failed to get pool_attr for NETFS diskpool type")
            return status, pool_attr

        pool_attr['Host'] = host_addr
        pool_attr['SourceDirectory'] = src_mnt_dir
        pool_attr['Path'] = dir_mnt_dir

    return PASS, pool_attr


@do_main(platform_sup)
def main():
    options = main.options
    server = options.ip
    virt = options.virt

    dp_types =  { }

    libvirt_version = virsh_version(server, virt)
    if libvirt_version < "0.4.1":
        logger.info("Storage pool creation support is available in Libvirt "
                    "version >= 0.4.1 , hence skipping the test....")
        return SKIP
    
    curr_cim_rev, changeset = get_provider_version(virt, server)
    if curr_cim_rev >= libvirt_disk_pool_support:
        dp_types["DISK_POOL_DIR"] =  1
    if curr_cim_rev >= libvirt_netfs_pool_support:
         dp_types["DISK_POOL_NETFS"] = 3

    if len(dp_types) == 0 :
        logger.info("No disk pool types in list , hence skipping the test...")
        return SKIP
    
    status = FAIL     
    pool_attr = None
    # For now the test case support only the creation of 
    # dir type disk pool, netfs later change to fs and disk pooltypes etc 
    for key, value in dp_types.iteritems():    
        try:
            logger.info("Verifying '%s'.....", key)
            test_pool = key
            status, pool_attr = get_pool_attr(server, value, dp_types, 
                                              curr_cim_rev)
            if status != PASS:
                return FAIL

            status = create_pool(server, virt, test_pool, pool_attr, 
                                 mode_type=value, pool_type= "DiskPool")

            if status != PASS:
                raise Exception("Failed to create '%s' type diskpool '%s'" \
                                 % (key, test_pool))

            status = verify_pool(server, virt, test_pool, pool_attr, 
                                 mode_type=value, pool_type="DiskPool")
            if status != PASS:
                destroy_diskpool(server, virt, test_pool)
                undefine_diskpool(server, virt, test_pool)
                raise Exception("Error in diskpool verification")

            status = destroy_diskpool(server, virt, test_pool)
            if status != PASS:
                raise Exception("Unable to destroy diskpool '%s'" \
                                % test_pool)

            status = undefine_diskpool(server, virt, test_pool)
            if status != PASS:
                raise Exception("Unable to undefine diskpool '%s'" \
                               % test_pool)

            if key == 'DISK_POOL_NETFS':
                netfs_cleanup(server, pool_attr)

            status = PASS

        except Exception, details:
            if status == PASS:
                status = FAIL

            logger.error("Exception details: %s", details)
            if key == 'DISK_POOL_NETFS':
                netfs_cleanup(server, pool_attr)
 
    return status

if __name__ == "__main__":
    sys.exit(main())
