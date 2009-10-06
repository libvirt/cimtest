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
# This test case verifies the deletion of the StorageVol using the 
# DeleteResourceInPool method of RPCS.
#
#                                                        -Date: 08-09-2009

import sys
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS, SKIP
from XenKvmLib.xm_virt_util import virsh_version
from XenKvmLib.const import do_main, platform_sup, get_provider_version, \
                            default_pool_name
from XenKvmLib import rpcs_service
from XenKvmLib.classes import get_typed_class, inst_to_mof
from XenKvmLib.pool import create_pool, DIR_POOL, \
                           libvirt_rasd_spool_del_changes, get_diskpool, \
                           get_stovol_default_settings, cleanup_pool_vol,\
                           get_sto_vol_rasd_for_pool

pool_attr = { 'Path' : "/tmp" }
vol_name = "cimtest-vol.img"

@do_main(platform_sup)
def main():
    options = main.options
    server = options.ip
    virt = options.virt

    libvirt_ver = virsh_version(server, virt)
    cim_rev, changeset = get_provider_version(virt, server)
    if libvirt_ver < "0.4.1" or cim_rev < libvirt_rasd_spool_del_changes:
        logger.info("Storage Volume deletion support is available with Libvirt"
                    "version >= 0.4.1 and Libvirt-CIM rev '%s'", 
                    libvirt_rasd_spool_del_changes)
        return SKIP

    dp_cn = "DiskPool"
    exp_vol_path = "%s/%s" % (pool_attr['Path'], vol_name)

    # For now the test case support only the deletion of dir type based 
    # vol, we can extend dp_types to include netfs etc .....
    dp_types = { "DISK_POOL_DIR" : DIR_POOL }

    for pool_name, pool_type in dp_types.iteritems():    
        status = FAIL     
        res = del_res = [FAIL]
        clean_pool = True
        clean_vol = False
        try:
            if pool_type == DIR_POOL:
                pool_name = default_pool_name
                clean_pool = False
            else:
                status = create_pool(server, virt, pool_name, pool_attr, 
                                     mode_type=pool_type, pool_type=dp_cn)

                if status != PASS:
                    logger.error("Failed to create pool '%s'", pool_name)
                    return status

            sv_rasd = get_stovol_default_settings(virt, server, dp_cn, pool_name, 
                                                  exp_vol_path, vol_name)
            if sv_rasd == None:
                raise Exception("Failed to get the defualt StorageVolRASD info")

            sv_settings = inst_to_mof(sv_rasd)

            dp_inst = get_diskpool(server, virt, dp_cn, pool_name)
            if dp_inst == None:
                raise Exception("DiskPool instance for '%s' not found!" \
                                % pool_name)
  
            rpcs = get_typed_class(virt, "ResourcePoolConfigurationService")
            rpcs_conn = eval("rpcs_service." + rpcs)(server)
            res = rpcs_conn.CreateResourceInPool(Settings=sv_settings, 
                                                 Pool=dp_inst)
            if res[0] != PASS:
                raise Exception("Failed to create the Vol %s" % vol_name)

            res_settings = get_sto_vol_rasd_for_pool(virt, server, dp_cn, 
                                            pool_name, exp_vol_path)
            if res_settings == None:
                raise Exception("Failed to get the resource settings for '%s'" \
                                " Vol" % vol_name)

            resource_setting = inst_to_mof(res_settings) 
            del_res = rpcs_conn.DeleteResourceInPool(Resource=resource_setting,
                                                     Pool=dp_inst)

            res_settings = get_sto_vol_rasd_for_pool(virt, server, dp_cn, 
                                                     pool_name, exp_vol_path)
            if res_settings != None:
                clean_vol = True
                raise Exception("'%s' vol of '%s' pool was not deleted" \
                                  % (vol_name, pool_name))
            else:
                logger.info("Vol '%s' of '%s' pool deleted successfully by " 
                            "DeleteResourceInPool()", vol_name, pool_name)

            ret = cleanup_pool_vol(server, virt, pool_name, vol_name, 
                                   exp_vol_path, clean_pool, clean_vol)
            if del_res[0] == PASS and ret == PASS :
                status = PASS
            else:
                return FAIL

        except Exception, details:
            logger.error("Exception details: %s", details)
            status = FAIL
            cleanup_pool_vol(server, virt, pool_name, vol_name, 
                             exp_vol_path, clean_pool, clean_vol)

        
    return status
if __name__ == "__main__":
    sys.exit(main())
