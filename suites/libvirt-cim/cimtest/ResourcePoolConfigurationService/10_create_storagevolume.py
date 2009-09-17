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
# CreateResourceInPool method of RPCS.
#
#                                                   -Date: 21-08-2009

import sys
import os
from VirtLib import utils
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS, SKIP
from XenKvmLib.const import do_main, platform_sup, default_pool_name, \
                            get_provider_version
from XenKvmLib.vsms import RASD_TYPE_STOREVOL
from XenKvmLib.rasd import libvirt_rasd_storagepool_changes
from XenKvmLib import rpcs_service
from XenKvmLib.assoc import Associators
from XenKvmLib.enumclass import GetInstance, EnumNames
from XenKvmLib.xm_virt_util import virsh_version, vol_list, vol_delete
from XenKvmLib.classes import get_typed_class, inst_to_mof
from XenKvmLib.common_util import destroy_diskpool
from XenKvmLib.pool import create_pool, undefine_diskpool, DIR_POOL

pool_attr = { 'Path' : "/tmp" }
vol_name = "cimtest-vol.img"

def get_stovol_rasd_from_sdc(virt, server, dp_inst_id):
    rasd = None
    ac_cn = get_typed_class(virt, "AllocationCapabilities")
    an_cn = get_typed_class(virt, "SettingsDefineCapabilities")
    key_list = {"InstanceID" : dp_inst_id} 
    
    try:
        inst = GetInstance(server, ac_cn, key_list)
        rasd = Associators(server, an_cn, ac_cn, InstanceID=inst.InstanceID)
    except Exception, detail:
        logger.error("Exception: %s", detail)
        return FAIL, None

    return PASS, rasd

def get_stovol_settings(server, virt, dp_id, pool_name):
    status, dp_rasds = get_stovol_rasd_from_sdc(virt, server, dp_id) 
    if status != PASS:
        logger.error("Failed to get the StorageVol RASD's")
        return None

    for dpool_rasd in dp_rasds:
        if dpool_rasd['ResourceType'] == RASD_TYPE_STOREVOL and \
            'Default' in dpool_rasd['InstanceID']:

            dpool_rasd['PoolID'] =  dp_id
            dpool_rasd['Path'] = pool_attr['Path']
            dpool_rasd['VolumeName'] = vol_name
            break

    if not pool_name in dpool_rasd['PoolID']:
        return None

    stovol_settings = inst_to_mof(dpool_rasd)

    return stovol_settings
    
def get_diskpool(server, virt, dp_cn, dp_inst_id):
    disk_pool_inst = None
    dpool_cn = get_typed_class(virt, dp_cn)
    pools = EnumNames(server, dpool_cn)
    for pool in pools:
        if pool['InstanceID'] == dp_inst_id:
            disk_pool_inst = pool
            break

    return disk_pool_inst

def verify_vol(server, virt, pool_name, exp_vol_path, found):
    vols = vol_list(server, virt, pool_name)
    if vols == None:
        raise Exception("Failed to get the volume information")
    
    for vol in vols.split('\n'):
        res_vol_name, res_vol_path = vol.split()
        if res_vol_name != vol_name and res_vol_path != exp_vol_path:
            continue
        else:
            found += 1

    if found != 1:
        logger.error("Failed to get the vol information")

    return found 

def verify_sto_vol_rasd(virt, server, dp_inst_id, exp_vol_path):
    dv_rasds = []
    status, rasds = get_stovol_rasd_from_sdc(virt, server, dp_inst_id)
    if status != PASS:
        logger.error("Failed to get the StorageVol for '%s' vol", exp_vol_path)
        return FAIL

    for item in rasds:
        if item['Address'] == exp_vol_path and item['PoolID'] == dp_inst_id:
           dv_rasds.append(item)

    if len(dv_rasds) != 4:
        logger.error("Got '%s' StorageVolRASD's expected 4", len(dv_rasds))
        return FAIL

    return PASS


def cleanup_pool_vol(server, virt, pool_name, clean_pool, vol_path):
    status = res = FAIL
    ret = None
    try:
        ret = vol_delete(server, virt, vol_name, pool_name)
        if ret == None:
            logger.error("Failed to delete the volume '%s'", vol_name)

        if os.path.exists(vol_path):
            cmd = "rm -rf %s" % vol_path
            res, out = utils.run_remote(server, cmd)
            if res != 0:
                logger.error("'%s' was not removed, please remove it "
                             "manually", vol_path)

        if clean_pool == True:
            status = destroy_diskpool(server, virt, pool_name)
            if status != PASS:
                raise Exception("Unable to destroy diskpool '%s'" % pool_name)
            else:    
                status = undefine_diskpool(server, virt, pool_name)
                if status != PASS:
                    raise Exception("Unable to undefine diskpool '%s'" \
                                     % pool_name)


    except Exception, details:
        logger.error("Exception details: %s", details)
        status = FAIL

    if (ret == None and res != PASS) or (clean_pool == True and status != PASS):
        logger.error("Failed to clean the env.....")
        return FAIL
  
    return PASS

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

    dp_cn = "DiskPool"
    exp_vol_path = "%s/%s" % (pool_attr['Path'], vol_name)

    # For now the test case support only the creation of dir type based 
    # vol creation, we can extend dp_types to include netfs etc 
    dp_types = { "DISK_POOL_DIR" : DIR_POOL }

    for pool_name, pool_type in dp_types.iteritems():    
        status = FAIL     
        res = [FAIL]
        found = 0
        clean_pool=True
        try:
            if pool_type == DIR_POOL:
                pool_name = default_pool_name
                clean_pool=False
            else:
                status = create_pool(server, virt, pool_name, pool_attr, 
                                     mode_type=pool_type, pool_type="DiskPool")

                if status != PASS:
                    logger.error("Failed to create pool '%s'", pool_name)
                    return status

            dp_inst_id = "%s/%s" % (dp_cn, pool_name)
            stovol_settings = get_stovol_settings(server, virt, 
                                                  dp_inst_id, pool_name)
            if stovol_settings == None:
                raise Exception("Failed to get the defualt StorageVolRASD info")

            disk_pool_inst = get_diskpool(server, virt, dp_cn, dp_inst_id)
            if disk_pool_inst == None:
                raise Exception("DiskPool instance for '%s' not found!" \
                                % pool_name)
  
            rpcs = get_typed_class(virt, "ResourcePoolConfigurationService")
            rpcs_conn = eval("rpcs_service." + rpcs)(server)
            res = rpcs_conn.CreateResourceInPool(Settings=stovol_settings, 
                                                 Pool=disk_pool_inst)
            if res[0] != PASS:
                raise Exception("Failed to create the Vol %s" % vol_name)

            found = verify_vol(server, virt, pool_name, exp_vol_path, found)
            stovol_status = verify_sto_vol_rasd(virt, server, dp_inst_id, 
                                                exp_vol_path)

            ret = cleanup_pool_vol(server, virt, pool_name, 
                                   clean_pool, exp_vol_path)
            if res[0] == PASS and found == 1 and \
               ret == PASS and stovol_status == PASS:
                status = PASS
            else:
                return FAIL
        
        except Exception, details:
            logger.error("Exception details: %s", details)
            status = FAIL

        
    return status
if __name__ == "__main__":
    sys.exit(main())
