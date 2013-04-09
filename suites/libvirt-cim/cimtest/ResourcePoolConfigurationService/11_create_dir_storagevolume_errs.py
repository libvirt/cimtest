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
# The test case checks for the errors when:
# 1) FormatType field in the StoragePoolRASD set to value other than RAW_TYPE
# 2) Trying to create 2 Vol in the same Path
#
#                                                   -Date: 04-09-2009

import sys
from random import randint
from CimTest.Globals import logger
from XenKvmLib import rpcs_service
from pywbem.cim_types import Uint64
from pywbem import CIM_ERR_FAILED, CIMError
from XenKvmLib.xm_virt_util import virsh_version, virsh_version_cmp
from CimTest.ReturnCodes import FAIL, PASS, SKIP
from XenKvmLib.classes import get_typed_class, inst_to_mof
from XenKvmLib.rasd import libvirt_rasd_storagepool_changes
from XenKvmLib.const import do_main, platform_sup, get_provider_version, \
                            default_pool_name
from XenKvmLib.pool import RAW_VOL_TYPE, get_diskpool,\
                           get_stovol_default_settings, cleanup_pool_vol

dir_pool_attr = { "Path" : "/tmp" }
vol_name = "cimtest-vol.img"

INVALID_FTYPE = RAW_VOL_TYPE + randint(20,100)
exp_err_no = CIM_ERR_FAILED
exp_err_values = { 'INVALID_FTYPE': { 'msg'   : "Unable to generate XML "\
                                                "for new resource" },
		   'DUP_VOL_PATH' : { 'msg' : "Unable to create storage volume"}
                 }

def get_inputs(virt, server, dp_cn, key, exp_vol_path, pool_name):
    sv_rasd = dp_inst = None
    try:
        sv_rasd = get_stovol_default_settings(virt, server, dp_cn, 
                                              pool_name, exp_vol_path, 
                                              vol_name)
        if sv_rasd == None:
            raise Exception("Failed to get the defualt StorageVolRASD info")

        if key == "INVALID_FTYPE":
            sv_rasd['FormatType'] = Uint64(INVALID_FTYPE)

        sv_settings = inst_to_mof(sv_rasd)
        dp_inst = get_diskpool(server, virt, dp_cn, pool_name)
        if dp_inst == None:
            raise Exception("DiskPool instance for '%s' not found!" % pool_name)

    except Exception, details:
       logger.error("In get_inputs() Exception details: %s", details)
       return FAIL, None, None

    return PASS, sv_settings, dp_inst

def verify_vol_err(virt, server, dp_cn, key, exp_vol_path, pool_name):
    status, sv_settings, dp_inst = get_inputs(virt, server, dp_cn, key, 
                                              exp_vol_path, pool_name)
    if status != PASS:
        return status
    
    status = FAIL
    res = ret = [FAIL] 
    try:
        logger.info("Verifying err for '%s'...", key)
        rpcs = get_typed_class(virt, "ResourcePoolConfigurationService")
        rpcs_conn = eval("rpcs_service." + rpcs)(server)
        ret = rpcs_conn.CreateResourceInPool(Settings=sv_settings, 
                                             Pool=dp_inst)

        # For duplicate vol path verfication we should have been able to 
        # create the first dir pool successfully before attempting the next
        if key == 'DUP_VOL_PATH' and ret[0] == PASS:
            # Trying to create the vol in the same vol path should return
            # an error
            res = rpcs_conn.CreateResourceInPool(Settings=sv_settings, 
                                                 Pool=dp_inst)
         
    except CIMError, (err_no, err_desc):
        if res[0] != PASS and exp_err_values[key]['msg'] in err_desc \
           and exp_err_no == err_no:
            logger.error("Got the expected error message: '%s' with '%s'", 
                          err_desc, key)
            status = PASS
        else:
            logger.error("Failed to get the error message '%s'", 
                         exp_err_values[key]['msg'])

    if (res[0] == PASS and key == 'DUP_VOL_PATH') or \
       (ret[0] == PASS and key == 'INVALID_FTYPE'):
        logger.error("Should not have been able to create Vol %s", vol_name)

    return status

@do_main(platform_sup)
def main():
    options = main.options
    server = options.ip
    virt = options.virt

    libvirt_ver = virsh_version(server, virt)
    cim_rev, changeset = get_provider_version(virt, server)
    if virsh_version_cmp(libvirt_ver, "0.4.1") < 0 or \
       cim_rev < libvirt_rasd_storagepool_changes:
        logger.info("Storage Volume creation support is available with Libvirt" 
                    "version >= 0.4.1 and Libvirt-CIM rev '%s'", 
                    libvirt_rasd_storagepool_changes)
        return SKIP

    dp_types = ['DUP_VOL_PATH', 'INVALID_FTYPE'] 
    dp_cn = "DiskPool"
    exp_vol_path = "%s/%s" % (dir_pool_attr['Path'], vol_name)
    pool_name = default_pool_name

    try:
        # err_key will contain either INVALID_FTYPE/DUP_VOL_PATH
        # to be able access the err mesg
        for err_key in dp_types:
            clean_vol = False
            status = FAIL     
            status = verify_vol_err(virt, server, dp_cn,
                                    err_key, exp_vol_path, pool_name)
            if status != PASS :
                raise Exception("Failed to verify the Invlaid '%s'" % err_key)

            if err_key == 'DUP_VOL_PATH':
                clean_vol = True

            ret = cleanup_pool_vol(server, virt, pool_name, vol_name, 
                                   exp_vol_path, clean_vol=clean_vol)
            if ret != PASS:
                raise Exception("Failed to clean the env")

    except Exception, details:
        logger.error("In main() Exception details: %s", details)
        status = FAIL

    return status
if __name__ == "__main__":
    sys.exit(main())
