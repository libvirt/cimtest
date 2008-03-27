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

import sys
from XenKvmLib import enumclass
from CimTest.Globals import do_main
from CimTest.Globals import logger, log_param, CIM_ERROR_ENUMERATE, platform_sup
from CimTest.ReturnCodes import PASS, FAIL

@do_main(platform_sup)
def main():
    options = main.options
    log_param()

    pools = {}
    pt = ['MemoryPool', 'ProcessorPool', 'DiskPool', 'NetworkPool']
    try:
        key_list = ["InstanceID"]
        ac = enumclass.enumerate(options.ip,
                                 "AllocationCapabilities",
                                 key_list,
                                 options.virt)
        pools['MemoryPool'] = enumclass.enumerate(options.ip,
                                                  "MemoryPool",
                                                  key_list,
                                                  options.virt)
        pools['ProcessorPool'] = enumclass.enumerate(options.ip,
                                                     "ProcessorPool",
                                                     key_list,
                                                     options.virt)
        pools['DiskPool'] = enumclass.enumerate(options.ip,
                                                "DiskPool",
                                                key_list,
                                                options.virt)
        pools['NetworkPool'] = enumclass.enumerate(options.ip,
                                                   "NetworkPool",
                                                   key_list,
                                                   options.virt)
    except Exception:
        logger.error(CIM_ERROR_ENUMERATE, '%s_AllocationCapabilities' % options.virt)
        return FAIL
     
    acset = set([(x.InstanceID, x.ResourceType) for x in ac])
    poolset = set()
    for pl in pools.values():
        for x in pl:
            poolset.add((x.InstanceID, x.ResourceType))

    if len(acset) != len(poolset):
        logger.error(
                'AllocationCapabilities return %i instances, excepted %i'
                % (ac_size, pool_size))
        return FAIL
    zeroset = acset - poolset
    if len(zeroset) != 0:
        logger.error('AC is inconsistent with pools')
        return FAIL

    return PASS

if __name__ == "__main__":
    sys.exit(main())
