#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Kaitlin Rupert <karupert@us.ibm.com>
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
# This test verifies the enum of AC returns the same number of instances as 
# the number of instances returned by enum of:
#                          MemoryPool + ProcessorPool + DiskPool + NetworkPool. 
#

import sys
from XenKvmLib.enumclass import EnumInstances 
from XenKvmLib.const import do_main, platform_sup, get_provider_version
from CimTest.Globals import logger, CIM_ERROR_ENUMERATE
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.common_util import cleanup_restore 
from XenKvmLib.classes import get_typed_class

sup_types = ['Xen', 'KVM', 'XenFV', 'LXC']
input_graphics_pool_rev = 757

def enum_pools(ip, ac_cn, virt):
    pt = [get_typed_class(virt, 'MemoryPool'), 
          get_typed_class(virt, 'ProcessorPool'), 
          get_typed_class(virt, 'DiskPool'), 
          get_typed_class(virt, 'NetworkPool')]

    curr_cim_rev, changeset = get_provider_version(virt, ip)
    if curr_cim_rev >= input_graphics_pool_rev:
          pt.append(get_typed_class(virt, 'GraphicsPool'))
          pt.append(get_typed_class(virt, 'InputPool'))

    pools = {}

    try:
        for p_cn in pt:
            
            enum_list = EnumInstances(ip, p_cn)

            if len(enum_list) < 1:
                raise Exception("%s did not return any instances" % p_cn)

            for pool in enum_list:
                pools[pool.InstanceID] = pool 

    except Exception, details:
        logger.error(CIM_ERROR_ENUMERATE, ac_cn)
        logger.error(details)
        return pools, FAIL 

    if len(pools) < len(pt):
        logger.error("%d pools returned, exp at least %d", len(pools), len(pt))
        return pools, FAIL

    return pools, PASS

def compare_pool_to_ac(ac, pools, cn):
    try:
        for inst in ac:
            id = inst.InstanceID
            if pools[id].ResourceType != inst.ResourceType:
                logger.error("%s ResourceType %s, Pool ResourceType %s" % (cn,
                             inst.ResourceType, pools[id].ResourceType))
                return FAIL

    except Exception, details:
        logger.error("%s returned instance with unexpected InstanceID %s" % (cn,
                     details))
        return FAIL

    return PASS

@do_main(sup_types)
def main():
    options = main.options

    cn = get_typed_class(options.virt, 'AllocationCapabilities')

    try:
        ac = EnumInstances(options.ip, cn)

    except Exception, details:
        logger.error(CIM_ERROR_ENUMERATE, cn)
        logger.error(details)
        return FAIL

    pools, status = enum_pools(options.ip, cn, options.virt)
    if status != PASS:
        return status

    if len(ac) != len(pools):
        logger.error("%d %s insts != %d pool insts" % (len(ac), cn, len(pools)))
        return FAIL

    status = compare_pool_to_ac(ac, pools, cn)

    return status 

if __name__ == "__main__":
    sys.exit(main())
