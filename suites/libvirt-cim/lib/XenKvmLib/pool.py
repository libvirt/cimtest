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
from CimTest.Globals import logger, CIM_NS
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.classes import get_typed_class, inst_to_mof
from XenKvmLib.const import get_provider_version, default_pool_name 
from XenKvmLib.enumclass import EnumInstances, GetInstance
from XenKvmLib.assoc import Associators
from VirtLib.utils import run_remote
from XenKvmLib.xm_virt_util import virt2uri, net_list
from XenKvmLib import rpcs_service
import pywbem
from CimTest.CimExt import CIMClassMOF
from XenKvmLib.vxml import NetXML

cim_errno  = pywbem.CIM_ERR_NOT_SUPPORTED
cim_mname  = "CreateChildResourcePool"
input_graphics_pool_rev = 757
libvirt_cim_child_pool_rev = 837

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
    else:
        return None

def enum_pools(virt, ip):
    pool_list = ['ProcessorPool', 'MemoryPool', 'NetworkPool', 'DiskPool']

    curr_cim_rev, changeset = get_provider_version(virt, ip)
    if curr_cim_rev >= input_graphics_pool_rev:
        pool_list.append('GraphicsPool')
        pool_list.append('InputPool')

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
    cmd = "virsh -c %s vol-list %s | sed -e '1,2 d' -e '$ d'" % \
          (virt2uri(virt), default_pool_name)
    ret, out = run_remote(server ,cmd)
    if ret != 0:
        return None
    lines = out.split("\n")
    for line in lines:
        vol = line.split()[0]   
        cmd = "virsh -c %s vol-info --pool %s %s" % (virt2uri(virt), pooln, vol)
        ret, out = run_remote(server ,cmd)
        if ret == 0:
            volume = volume + 1

    return volume

def get_pool_rasds(server, virt):
    net_pool_rasds = []

    ac_cn = get_typed_class(virt, "AllocationCapabilities")
    an_cn = get_typed_class(virt, "SettingsDefineCapabilities")
    key_list = {"InstanceID" : "NetworkPool/0" }
    
    try:
        inst = GetInstance(server, ac_cn, key_list)
        rasd = Associators(server, an_cn, ac_cn, InstanceID=inst.InstanceID)
    except Exception, detail:
        logger.error("Exception: %s", detail)
        return None

    for item in rasd:
        if item['InstanceID'] == "Default":
           net_pool_rasds.append(item)

    return net_pool_rasds

def net_undefine(network, server, virt="Xen"):
    """Function undefine a given virtual network"""

    cmd = "virsh -c %s net-undefine %s" % (virt2uri(virt), network)
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

def create_netpool(server, virt, test_pool, pool_attr_list): 
    status = PASS
    rpcs = get_typed_class(virt, "ResourcePoolConfigurationService")
    rpcs_conn = eval("rpcs_service." + rpcs)(server)
    curr_cim_rev, changeset = get_provider_version(virt, server)
    if curr_cim_rev < libvirt_cim_child_pool_rev:
        try:
            rpcs_conn.CreateChildResourcePool()
        except pywbem.CIMError, (err_no, desc):
            if err_no == cim_errno :
                logger.info("Got expected exception for '%s'service", cim_mname)
                logger.info("Errno is '%s' ", err_no)
                logger.info("Error string is '%s'", desc)
                return PASS
            else:
                logger.error("Unexpected rc code %s and description %s\n",
                             err_no, desc)
                return FAIL
    elif curr_cim_rev >= libvirt_cim_child_pool_rev: 
        n_list = net_list(server, virt)
        for _net_name in n_list:
            net_xml = NetXML(server=server, networkname=_net_name, 
                             virt=virt, is_new_net=False)
            pool_use_attr = net_xml.xml_get_netpool_attr_list()
            if pool_attr_list['Address'] in pool_use_attr:
                logger.error("IP address is in use by a different network")
                return FAIL
        
        net_pool_rasds = get_pool_rasds(server, virt)
        if len(net_pool_rasds) == 0:
            logger.error("We can not get NetPoolRASDs")
            return FAIL
        else:
            net_pool_rasds[0]['PoolID'] = "NetworkPool/%s" % test_pool
            for attr, val in pool_attr_list.iteritems():
                net_pool_rasds[0][attr] = val
           
            pool_settings = inst_to_mof(net_pool_rasds[0])
            
        try:
            rpcs_conn.CreateChildResourcePool(ElementName=test_pool, 
                                              Settings=[pool_settings])
        except Exception, details:
            logger.error("Error in childpool creation")
            logger.error(details)
            return FAIL

        return status


def verify_pool(server, virt, pooltype, poolname, pool_attr_list):
    status = FAIL
    pool_list = EnumInstances(server, pooltype)
    if len(pool_list) < 1:
        logger.error("Return %i instances, expected at least one instance",
                     len(pool_list))
        return FAIL
    
    poolid = "NetworkPool/%s" % poolname
    for i in range(0, len(pool_list)):
        ret_pool = pool_list[i].InstanceID
        if ret_pool != poolid:
            continue

        net_xml = NetXML(server, virt=virt, networkname=poolname, 
                         is_new_net=False)
        ret_pool_attr_list = net_xml.xml_get_netpool_attr_list()
        
        for i in range(0, len(ret_pool_attr_list)):
            if ret_pool_attr_list[i] not in pool_attr_list.itervalues():
                logger.error("Got error when parsing %s", ret_pool_attr_list[i])
                return FAIL

            status = PASS

    return status
