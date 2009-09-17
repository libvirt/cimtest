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
#
# This test case verifies the creation of the StorageVol using the 
# CreateResourceInPool method of RPCS returns an error when invalid values
# are passed.
# The test case checks for the errors when,
# Trying to create a Vol in a netfs storage pool
#
#                                                   -Date: 04-09-2009

import sys
from pywbem import CIM_ERR_FAILED, CIMError
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS, SKIP
from XenKvmLib.const import do_main, platform_sup, get_provider_version
from XenKvmLib.rasd import libvirt_rasd_storagepool_changes
from XenKvmLib import rpcs_service
from XenKvmLib.xm_virt_util import virsh_version
from XenKvmLib.classes import get_typed_class, inst_to_mof
from XenKvmLib.common_util import nfs_netfs_setup, netfs_cleanup
from XenKvmLib.pool import create_pool, NETFS_POOL, get_diskpool, \
                           get_stovol_default_settings, cleanup_pool_vol

vol_name = "cimtest-vol.img"
vol_path = "/tmp/"

exp_err_no = CIM_ERR_FAILED
exp_err_values = { 'NETFS_POOL'   : { 'msg'   : "This function does not "\
                                                "support this resource type"}
                 }

def get_pool_attr(server, pool_type):
    pool_attr = { }
    status , host_addr, src_mnt_dir, dir_mnt_dir = nfs_netfs_setup(server)
    if status != PASS:
        logger.error("Failed to get pool_attr for NETFS diskpool type")
        return status, pool_attr

    pool_attr['Host'] = host_addr
    pool_attr['SourceDirectory'] = src_mnt_dir
    pool_attr['Path'] = dir_mnt_dir

    return PASS, pool_attr

def get_inputs(virt, server, dp_cn, pool_name, exp_vol_path):
    sv_rasd = dp_inst = None
    try:
        sv_rasd = get_stovol_default_settings(virt, server, dp_cn, pool_name, 
                                              exp_vol_path, vol_name)
        if sv_rasd == None:
            raise Exception("Failed to get the defualt StorageVolRASD info")

        sv_settings = inst_to_mof(sv_rasd)

        dp_inst = get_diskpool(server, virt, dp_cn, pool_name)
        if dp_inst == None:
            raise Exception("DiskPool instance for '%s' not found!" \
                            % pool_name)

    except Exception, details:
        logger.error("Exception details: %s", details)
        return FAIL, sv_rasd, dp_inst

    return PASS, sv_settings, dp_inst

def verify_vol_err(server, virt, dp_cn, pool_name, exp_vol_path): 

    status, sv_settings, dp_inst = get_inputs(virt, server, dp_cn, 
                                              pool_name, exp_vol_path)
    if status != PASS:
        return status
     
    status = FAIL
    res = [FAIL] 
    try:
        rpcs = get_typed_class(virt, "ResourcePoolConfigurationService")
        rpcs_conn = eval("rpcs_service." + rpcs)(server)
        res = rpcs_conn.CreateResourceInPool(Settings=sv_settings, 
                                             Pool=dp_inst)

    except CIMError, (err_no, err_desc):
        if res[0] != PASS and exp_err_values[pool_name]['msg'] in err_desc \
           and exp_err_no == err_no:
            logger.error("Got the expected error message: '%s' with '%s'", 
                          err_desc, pool_name)
            return PASS
        else:
            logger.error("Failed to get the error message '%s'", 
                         exp_err_values[pool_name]['msg'])
    if res[0] == PASS:
        logger.error("Should not have been able to create the StorageVol '%s'", 
                      vol_name)

    return FAIL


@do_main(platform_sup)
def main():
    options = main.options
    server = options.ip
    virt = options.virt

    libvirt_ver = virsh_version(server, virt)
    cim_rev, changeset = get_provider_version(virt, server)
    if libvirt_ver < "0.4.1" and cim_rev < libvirt_rasd_storagepool_changes:
        logger.info("Storage Volume creation support is available with Libvirt" 
                    "version >= 0.4.1 and Libvirt-CIM rev '%s'", 
                    libvirt_rasd_storagepool_changes)
        return SKIP

    pool_name =  "NETFS_POOL"
    pool_type = NETFS_POOL
    exp_vol_path = "%s/%s" % (vol_path, vol_name)
    dp_cn = "DiskPool"
    clean_pool = False   

    try:
        status = FAIL     
        status, pool_attr = get_pool_attr(server, pool_type)
        if status != PASS:
            return status

        # Creating NETFS pool to verify RPCS error
        status = create_pool(server, virt, pool_name, pool_attr, 
                             mode_type=pool_type, pool_type=dp_cn)

        if status != PASS:
            logger.error("Failed to create pool '%s'", pool_name)
            return status

        clean_pool = True
        status = verify_vol_err(server, virt, dp_cn, pool_name, exp_vol_path)
        if status != PASS :
            raise Exception("Failed to verify the Invlaid '%s' " % pool_name)

        
    except Exception, details:
        logger.error("Exception details: %s", details)
        status = FAIL

    ret = cleanup_pool_vol(server, virt, pool_name, vol_name, exp_vol_path,
                           clean_pool)
    netfs_cleanup(server, pool_attr)
    if status != PASS or ret != PASS :
        return FAIL
        
    return PASS
if __name__ == "__main__":
    sys.exit(main())
