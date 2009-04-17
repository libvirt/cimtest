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
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.classes import get_typed_class
from XenKvmLib.const import get_provider_version, default_pool_name 
from XenKvmLib.enumclass import EnumInstances
from VirtLib.utils import run_remote
from XenKvmLib.xm_virt_util import virt2uri

input_graphics_pool_rev = 757

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

