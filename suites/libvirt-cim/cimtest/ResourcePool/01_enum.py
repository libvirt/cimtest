#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Deepti B.Kalakeri <dkalaker@in.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Veerendra Chandrappa <vechandr@in.ibm.com>
#    Zhengang Li <lizg@cn.ibm.com>
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
from distutils.file_util import move_file
from XenKvmLib.enumclass import EnumInstances
from XenKvmLib.classes import get_typed_class
from XenKvmLib import vxml
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE
from XenKvmLib.const import do_main, default_pool_name, LXC_netns_support
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from XenKvmLib.xm_virt_util import net_list
from XenKvmLib.vsms import RASD_TYPE_PROC, RASD_TYPE_MEM, RASD_TYPE_NET_ETHER, \
RASD_TYPE_DISK 

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']

dp_cn = 'DiskPool'
mp_cn = 'MemoryPool'
pp_cn = 'ProcessorPool'
np_cn = 'NetworkPool'

def init_list(server, virt):
   # Verify the Virtual network on machine
    vir_network = net_list(server, virt)
    if len(vir_network) > 0:
        test_network = vir_network[0]
    else:
        bridgename   = 'testbridge'
        test_network = 'default-net'
        netxml = vxml.NetXML(server, bridgename, test_network, virt)
        ret = netxml.create_vnet()
        if not ret:
            logger.error("Failed to create the Virtual Network '%s'",
                          test_network)
            return SKIP, None

    disk_instid = '%s/%s' % (dp_cn, default_pool_name)
    net_instid = '%s/%s' % (np_cn, test_network)
    mem_instid = '%s/0' % mp_cn
    proc_instid = '%s/0' % pp_cn
    pool_list = {
            get_typed_class(virt, mp_cn) : [mem_instid, RASD_TYPE_MEM],
            get_typed_class(virt, pp_cn) : [proc_instid, RASD_TYPE_PROC],
            get_typed_class(virt, dp_cn) : [disk_instid, RASD_TYPE_DISK],
            get_typed_class(virt, np_cn) : [net_instid, RASD_TYPE_NET_ETHER]
            } 
    return PASS, pool_list

def print_error(fieldname="", ret_value="", exp_value=""):
    logger.error("%s Mismatch", fieldname)
    logger.error("Returned %s instead of %s", ret_value, exp_value)

def verify_fields(pool_list, poolname, cn):
    if len(poolname) < 1:
        logger.error("%s return %i instances, expected atleast 1 instance",
                     cn, len(poolname))
        return FAIL

    for i in range(0, len(poolname)):

        rtype_ret_value = poolname[i].ResourceType
        rtype_exp_value = pool_list[cn][1]
        if rtype_ret_value != rtype_exp_value:
            print_error('ResourceType', rtype_ret_value, rtype_exp_value)
            return FAIL

        inst_ret_value = poolname[i].InstanceID
        inst_exp_value = pool_list[cn][0]
        if "DiskPool/0" == inst_ret_value or "NetworkPool/0" == inst_ret_value:
            if poolname[i].Primordial != True:
                print_error('Primordial', poolname[i].Primordial, "True")
                return FAIL
        elif inst_ret_value != inst_exp_value and i == len(poolname)-1:
            print_error('InstanceID', inst_ret_value, inst_exp_value)
            return FAIL

    return PASS


@do_main(sup_types)
def main():
    ip = main.options.ip
    if main.options.virt == "XenFV":
        virt = "Xen"
    else:
        virt = main.options.virt

    status, pool_list = init_list(ip, virt)
    if status != PASS: 
        logger.error("Failed to initialise the list")
        return status

    mp = get_typed_class(virt, mp_cn)
    pp = get_typed_class(virt, pp_cn)
    dp = get_typed_class(virt, dp_cn)
    cn_list = [ mp, pp, dp ]

    if virt == 'LXC' and LXC_netns_support is False:
        pass
    else:
        np = get_typed_class(virt, np_cn)
        cn_list.append(np)

    for cn in cn_list:
        try:
            pool = EnumInstances(ip, cn)
        except Exception, details:
            logger.error(CIM_ERROR_ENUMERATE, cn)
            logger.error("Exception details: %s", details)
            return FAIL
        status = verify_fields(pool_list, pool, cn)
        if status != PASS:
            return status
    return status

if __name__ == "__main__":
    sys.exit(main())
