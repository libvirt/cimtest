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
# DeleteResourceInPool method of RPCS returns error when invalid values are 
# passed.
#
#                                                   -Date: 08-09-2009

import sys
import os
from VirtLib import utils
from CimTest.Globals import logger
from pywbem import CIM_ERR_FAILED, CIM_ERR_INVALID_PARAMETER, CIMError
from CimTest.ReturnCodes import FAIL, PASS, SKIP
from XenKvmLib.xm_virt_util import virsh_version, virsh_version_cmp
from XenKvmLib.const import do_main, platform_sup, get_provider_version,\
                            default_pool_name, _image_dir
from XenKvmLib import rpcs_service
from XenKvmLib.classes import get_typed_class, inst_to_mof
from XenKvmLib.pool import create_pool, DIR_POOL, \
                           libvirt_rasd_spool_del_changes, get_diskpool, \
                           get_stovol_default_settings, cleanup_pool_vol, \
                           get_sto_vol_rasd_for_pool

pool_attr = { 'Path' : _image_dir }
vol_name = "cimtest-vol.img"
invalid_scen = { "INVALID_ADDRESS"  :  { 'val' : 'Junkvol_path',
                                         'msg' : 'no storage vol with '\
                                                'matching path' },
                 "NO_ADDRESS_FIELD" :  { 'msg' :'Missing Address in '\
                                                'resource RASD' },
                 "MISSING_RESOURCE"  : { 'msg' :"Missing argument `Resource'"},
                 "MISSING_POOL"      : { 'msg' :"Missing argument `Pool'"}
               }
                                           

def verify_rpcs_err_val(virt, server, rpcs_conn, dp_cn, pool_name, 
                        exp_vol_path, dp_inst):

    for err_scen in invalid_scen.keys():    
        logger.info("Verifying errors for '%s'....", err_scen)
        status = FAIL
        del_res = [FAIL] 
        try:
            res_settings = get_sto_vol_rasd_for_pool(virt, server, dp_cn, 
                                                     pool_name, exp_vol_path)
            if res_settings == None:
                raise Exception("Failed getting resource settings for '%s' vol"\
                                " when executing '%s'" % (vol_name, err_scen))
            
            if not "MISSING" in err_scen:
                exp_err_no = CIM_ERR_FAILED

                if "NO_ADDRESS_FIELD" in err_scen:
                    del res_settings['Address'] 
                elif "INVALID_ADDRESS" in err_scen:
                    res_settings['Address'] = invalid_scen[err_scen]['val']

                resource = inst_to_mof(res_settings) 
                del_res = rpcs_conn.DeleteResourceInPool(Resource=resource,
                                                         Pool=dp_inst)
            else:
                exp_err_no = CIM_ERR_INVALID_PARAMETER

                if err_scen == "MISSING_RESOURCE":
                    del_res = rpcs_conn.DeleteResourceInPool(Pool=dp_inst)
                elif err_scen == "MISSING_POOL":
                    resource = inst_to_mof(res_settings) 
                    del_res = rpcs_conn.DeleteResourceInPool(Resource=resource)

        except CIMError, (err_no, err_desc):
            if del_res[0] != PASS and invalid_scen[err_scen]['msg'] in err_desc\
               and exp_err_no == err_no:
                logger.error("Got the expected error message: '%s' for '%s'", 
                              err_desc, err_scen)
                status = PASS
            else:
                logger.error("Unexpected error msg, Expected '%s'-'%s', Got"
                             "'%s'-'%s'", exp_err_no, 
                              invalid_scen[err_scen]['msg'], err_no, err_desc)
                return FAIL
                             
        except Exception, details:
            logger.error("Exception details: %s", details)
            return FAIL

        if del_res[0] == PASS or status != PASS:
            logger.error("Should not have been able to delete Vol %s", vol_name)
            return FAIL

    return status

@do_main(platform_sup)
def main():
    options = main.options
    server = options.ip
    virt = options.virt

    libvirt_ver = virsh_version(server, virt)
    cim_rev, changeset = get_provider_version(virt, server)
    if virsh_version_cmp(libvirt_ver, "0.4.1") < 0 or \
       cim_rev < libvirt_rasd_spool_del_changes:
        logger.info("Storage Volume deletion support is available with Libvirt"
                    "version >= 0.4.1 and Libvirt-CIM rev '%s'", 
                    libvirt_rasd_spool_del_changes)
        return SKIP

    dp_cn = "DiskPool"
    exp_vol_path = "%s/%s" % (pool_attr['Path'], vol_name)

    pool_name = default_pool_name
    status = FAIL     
    res = del_res = [FAIL]
    clean_vol = False
   
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

        rpcs = get_typed_class(virt, "ResourcePoolConfigurationService")
        rpcs_conn = eval("rpcs_service." + rpcs)(server)
        res = rpcs_conn.CreateResourceInPool(Settings=sv_settings, 
                                             Pool=dp_inst)
        if res[0] != PASS:
            raise Exception("Failed to create the Vol %s" % vol_name)

        status = verify_rpcs_err_val(virt, server, rpcs_conn, dp_cn, 
                                     pool_name, exp_vol_path, dp_inst)
        if status != PASS :
            clean_vol = True
            raise Exception("Verification Failed for DeleteResourceInPool()")

    except Exception, details:
        logger.error("Exception details: %s", details)
        status = FAIL

    ret = cleanup_pool_vol(server, virt, pool_name, vol_name, exp_vol_path,
                           clean_vol)
    if status != PASS or ret != PASS:
        return FAIL
        
    return status
if __name__ == "__main__":
    sys.exit(main())
