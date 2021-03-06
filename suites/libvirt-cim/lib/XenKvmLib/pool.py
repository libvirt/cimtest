#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Kaitlin Rupert <karupert@us.ibm.com>
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

import sys
import os
from VirtLib import utils
from CimTest.Globals import logger, CIM_NS
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from XenKvmLib.classes import get_typed_class, inst_to_mof
from XenKvmLib.const import get_provider_version, default_pool_name 
from XenKvmLib.enumclass import EnumInstances, GetInstance, EnumNames
from XenKvmLib.assoc import Associators
from VirtLib.utils import run_remote
from XenKvmLib.xm_virt_util import virt2uri, net_list, vol_delete
from XenKvmLib import rpcs_service
import pywbem
from CimTest.CimExt import CIMClassMOF
from XenKvmLib.vxml import NetXML, PoolXML
from XenKvmLib.xm_virt_util import virsh_version, virsh_version_cmp
from XenKvmLib.vsms import RASD_TYPE_STOREVOL
from XenKvmLib.common_util import destroy_diskpool

cim_errno  = pywbem.CIM_ERR_NOT_SUPPORTED
cim_mname  = "CreateChildResourcePool"
input_graphics_pool_rev = 757
libvirt_cim_child_pool_rev = 837
libvirt_rasd_spool_del_changes = 971
libvirt_controller_rev = 1312

DIR_POOL = 1L
FS_POOL = 2L
NETFS_POOL = 3L
DISK_POOL = 4L
ISCSI_POOL = 5L
LOGICAL_POOL = 6L
SCSI_POOL = 7L

#Volume types
RAW_VOL_TYPE = 1

def pool_cn_to_rasd_cn(pool_cn, virt):
    if pool_cn.find('ProcessorPool') >= 0:
        return get_typed_class(virt, "ProcResourceAllocationSettingData")
    elif pool_cn.find('NetworkPool') >= 0:
        return get_typed_class(virt, "NetResourceAllocationSettingData")
    elif pool_cn.find('DiskPool') >= 0:
        return get_typed_class(virt, "DiskResourceAllocationSettingData")
    elif pool_cn.find('MemoryPool') >= 0:
        return get_typed_class(virt, "MemResourceAllocationSettingData")
    elif pool_cn.find('GraphicsPool') >= 0:
        return get_typed_class(virt, "GraphicsResourceAllocationSettingData")
    elif pool_cn.find('InputPool') >= 0:
        return get_typed_class(virt, "InputResourceAllocationSettingData")
    elif pool_cn.find('ControllerPool') >= 0:
        return get_typed_class(virt, "ControllerResourceAllocationSettingData")
    else:
        return None

def enum_pools(virt, ip):
    pool_list = ['ProcessorPool', 'MemoryPool', 'NetworkPool', 'DiskPool']

    curr_cim_rev, changeset = get_provider_version(virt, ip)
    if curr_cim_rev >= input_graphics_pool_rev:
        pool_list.append('GraphicsPool')
        pool_list.append('InputPool')

    if curr_cim_rev >= libvirt_controller_rev and virt == 'KVM':
        pool_list.append('ControllerPool')

    pool_insts = {}

    try:
        for pool in pool_list:
            pool_cn = get_typed_class(virt, pool)
            list = EnumInstances(ip, pool_cn)

            if len(list) < 1:
                raise Exception("%s did not return any instances" % pool_cn)

            for pool in list:
                if pool.Classname not in pool_insts.keys():
                    pool_insts[pool.Classname] = []
                pool_insts[pool.Classname].append(pool)

        if len(pool_insts) != len(pool_list):
            raise Exception("Got %d pool insts, exp %d" % (len(pool_insts),
                            len(pool_list)))

    except Exception, details:
        logger.error(details)
        return pool_insts, FAIL

    return pool_insts, PASS

def enum_volumes(virt, server, pooln=default_pool_name):
    volume = 0
    cmd = 'virsh -c %s vol-list %s 2>/dev/null | sed -e "1,2 d" -e "$ d"' % \
          (virt2uri(virt), pooln)
    ret, out = run_remote(server ,cmd)
    if ret != 0 or len(out) == 0:
        return volume
    lines = out.split("\n")
    for line in lines:
        vol = line.split()[0]   
        cmd = "virsh -c %s vol-info --pool %s %s 2>/dev/null" % \
              (virt2uri(virt), pooln, vol)
        ret, out = run_remote(server ,cmd)
        if ret == 0:
            volume = volume + 1

    return volume

def get_pool_rasds(server, virt, pool_type="NetworkPool", filter_default=True):

    net_pool_rasd_rev = 867 
    disk_pool_rasd_rev = 863 

    try:
        rev, changeset = get_provider_version(virt, server)
        if pool_type == "NetworkPool" and rev < net_pool_rasd_rev:
            raise Exception("Supported in version %d" % net_pool_rasd_rev)
 
        if pool_type == "DiskPool" and rev < disk_pool_rasd_rev:
            raise Exception("Supported in version %d" % disk_pool_rasd_rev)

    except Exception, detail:
        logger.error("%s template RASDs not supported. %s.", pool_type, detail)
        return SKIP, None

    n_d_pool_rasds = []

    ac_cn = get_typed_class(virt, "AllocationCapabilities")
    an_cn = get_typed_class(virt, "SettingsDefineCapabilities")
    key_list = {"InstanceID" : "%s/0" %pool_type }
    
    try:
        inst = GetInstance(server, ac_cn, key_list)
        rasd = Associators(server, an_cn, ac_cn, InstanceID=inst.InstanceID)
    except Exception, detail:
        logger.error("Exception: %s", detail)
        return FAIL, None
     
    if filter_default == True:
        for item in rasd:
            if item['InstanceID'] == "Default":
               n_d_pool_rasds.append(item)
    else:
        return PASS, rasd

    return PASS, n_d_pool_rasds

def net_undefine(network, server, virt="Xen"):
    """Function undefine a given virtual network"""

    cmd = "virsh -c %s net-undefine %s 2>/dev/null" % (virt2uri(virt), network)
    ret, out = run_remote(server, cmd)

    return ret

def undefine_netpool(server, virt, net_name):
    if net_name == None:
       return FAIL

    ret = net_undefine(net_name, server, virt)
    if ret != 0:
        logger.error("Failed to undefine Virtual Network '%s'", net_name)
        return FAIL

    return PASS    

def undefine_diskpool(server, virt, dp_name):
    libvirt_version = virsh_version(server, virt)
    if virsh_version_cmp(libvirt_version, '0.4.1') >= 0:
        if dp_name == None:
           return FAIL

        cmd = "virsh -c %s pool-undefine %s 2>/dev/null" % \
              (virt2uri(virt), dp_name)
        ret, out = run_remote(server, cmd)
        if ret != 0:
            logger.error("Failed to undefine pool '%s'", dp_name)
            return FAIL

    return PASS    

def create_pool(server, virt, test_pool, pool_attr_list, 
                mode_type=0, pool_type="NetworkPool"): 

    rpcs = get_typed_class(virt, "ResourcePoolConfigurationService")
    rpcs_conn = eval("rpcs_service." + rpcs)(server)
    curr_cim_rev, changeset = get_provider_version(virt, server)
    if curr_cim_rev < libvirt_cim_child_pool_rev:

        try:
            rpcs_conn.CreateChildResourcePool()
        except pywbem.CIMError, (err_no, desc):
            if err_no == cim_errno:
                logger.info("Got expected exception for '%s'service", cim_mname)
                logger.info("Errno is '%s' ", err_no)
                logger.info("Error string is '%s'", desc)
                return PASS
            else:
                logger.error("Unexpected rc code %s and description %s\n",
                             err_no, desc)
                return FAIL

    elif curr_cim_rev >= libvirt_cim_child_pool_rev: 

        if pool_type == "NetworkPool" :
            n_list = net_list(server, virt)
            for _net_name in n_list:
                net_xml = NetXML(server=server, networkname=_net_name, 
                                 virt=virt, is_new_net=False)
                pool_use_attr = net_xml.xml_get_netpool_attr_list()
                if pool_attr_list['Address'] in pool_use_attr:
                    logger.error("IP address is in use by a different network")
                    return FAIL
        
        status, n_d_pool_rasds = get_pool_rasds(server, virt, pool_type)
        if status != PASS:
            return status 

        if len(n_d_pool_rasds) == 0:
            logger.error("Failed to get '%sRASD'", pool_type)
            return FAIL
        else:
            for i in range(0, len(n_d_pool_rasds)):
                pool_id = "%s/%s" %(pool_type, test_pool)
                n_d_pool_rasds[i]['PoolID'] = pool_id 
                if pool_type == "NetworkPool":
                    key = 'ForwardMode'
                elif  pool_type == "DiskPool": 
                    key = 'Type'

                if n_d_pool_rasds[i][key] == mode_type:
                   for attr, val in pool_attr_list.iteritems():
                       n_d_pool_rasds[i][attr] = val
                   break
 
            pool_settings = inst_to_mof(n_d_pool_rasds[i])
            
        try:
            rpcs_conn.CreateChildResourcePool(ElementName=test_pool, 
                                              Settings=[pool_settings])
        except Exception, details:
            logger.error("Exception in create_pool()")
            logger.error("Exception details: %s", details)
            return FAIL

        return PASS

def verify_pool(server, virt, poolname, pool_attr_list, mode_type=0,
                pool_type="NetworkPool"):
    status = FAIL
    pool_cn = get_typed_class(virt, pool_type) 
    pool_list = EnumInstances(server, pool_cn)
    if len(pool_list) < 1:
        logger.error("Got %i instances, expected at least one instance",
                      len(pool_list))
        return FAIL
    
    poolid = "%s/%s" % (pool_type, poolname)
    for i in range(0, len(pool_list)):
        ret_pool = pool_list[i].InstanceID
        if ret_pool != poolid:
            continue

        if pool_type == "NetworkPool":
            net_xml = NetXML(server, virt=virt, networkname=poolname, 
                             is_new_net=False)
      
            ret_mode = net_xml.xml_get_netpool_mode()
            libvirt_version = virsh_version(server, virt)
            #Forward mode support was added in 0.4.2
            if virsh_version_cmp(libvirt_version, '0.4.2') >= 0:
                if mode_type == 1 and ret_mode != "nat":
                    logger.error("Error when verifying 'nat' type network")
                    return FAIL
                elif mode_type == 2 and ret_mode != "route":
                    logger.error("Error when verifying 'route' type network")
                    return FAIL
            ret_pool_attr_list = net_xml.xml_get_netpool_attr_list()

        elif pool_type == "DiskPool":
            disk_xml = PoolXML(server ,virt=virt, poolname=poolname,
                               is_new_pool=False)
            ret_pool_attr_list = disk_xml.xml_get_pool_attr_list()
        
        for i in range(0, len(ret_pool_attr_list)):
            if ret_pool_attr_list[i] not in pool_attr_list.itervalues():
                logger.error("Failed to verify '%s'", ret_pool_attr_list[i])
                return FAIL

            status = PASS

    return status

def get_stovol_rasd_from_sdc(virt, server, dp_inst_id):
    rasd = None
    ac_cn = get_typed_class(virt, "AllocationCapabilities")
    an_cn = get_typed_class(virt, "SettingsDefineCapabilities")
    key_list = {"InstanceID" : dp_inst_id} 
    
    try:
        inst = GetInstance(server, ac_cn, key_list)
        if inst == None:
            raise Exception("Failed to GetInstance for %s" % dp_inst_id)

        rasd = Associators(server, an_cn, ac_cn, InstanceID=inst.InstanceID)
        if len(rasd) < 4:
            raise Exception("Failed to get default StorageVolRASD , "\
                            "Expected atleast 4, Got '%s'" % len(rasd))

    except Exception, detail:
        logger.error("Exception: %s", detail)
        return FAIL, None

    return PASS, rasd

def get_stovol_default_settings(virt, server, dp_cn,
                                pool_name, path, vol_name):

    dp_inst_id = "%s/%s" % (dp_cn, pool_name)
    status, dp_rasds = get_stovol_rasd_from_sdc(virt, server, dp_inst_id) 
    if status != PASS:
        logger.error("Failed to get the StorageVol RASD's")
        return None

    for dpool_rasd in dp_rasds:
        if dpool_rasd['ResourceType'] == RASD_TYPE_STOREVOL and \
            'Default' in dpool_rasd['InstanceID']:

            dpool_rasd['PoolID'] =  dp_inst_id
            dpool_rasd['Path'] = path 
            dpool_rasd['VolumeName'] = vol_name
            break

    if not pool_name in dpool_rasd['PoolID']:
        return None

    return dpool_rasd

def get_diskpool(server, virt, dp_cn, pool_name):
    dp_inst = None
    dpool_cn = get_typed_class(virt, dp_cn)
    pools = EnumNames(server, dpool_cn)

    dp_inst_id = "%s/%s" % (dp_cn, pool_name)
    for pool in pools:
        if pool['InstanceID'] == dp_inst_id:
            dp_inst = pool
            break

    return dp_inst

def get_sto_vol_rasd_for_pool(virt, server, dp_cn, pool_name, exp_vol_path):
    dv_rasds = None 
    dp_inst_id = "%s/%s" % (dp_cn, pool_name)
    status, rasds = get_stovol_rasd_from_sdc(virt, server, dp_inst_id)
    if status != PASS:     
        logger.error("Failed to get the StorageVol for '%s' vol", exp_vol_path)
        return FAIL

    for item in rasds:
        if item['Address'] == exp_vol_path and item['PoolID'] == dp_inst_id:
           dv_rasds = item
           break 
    
    return dv_rasds

def cleanup_pool_vol(server, virt, pool_name, vol_name, 
                     vol_path, clean_pool=False, clean_vol=False):
    status = res = FAIL
    ret = None
    try:

        if clean_vol == True:
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

    if (clean_vol == True and ret == None) or \
       (clean_pool == True and status != PASS):
        logger.error("Failed to clean the env.....")
        return FAIL
  
    return PASS
