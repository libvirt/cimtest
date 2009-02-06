#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
#    Zhengang Li <lizg@cn.ibm.com>
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
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
from XenKvmLib.assoc import AssociatorNames 
from XenKvmLib import enumclass
from XenKvmLib.common_util import get_host_info
from XenKvmLib.const import default_network_name
from CimTest import Globals
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.const import do_main, default_pool_name
from XenKvmLib.classes import get_typed_class

sup_types=['Xen', 'KVM', 'XenFV', 'LXC']
@do_main(sup_types)
def main():
    options = main.options
    status = PASS

    keys = ['Name', 'CreationClassName']
    status, host_inst = get_host_info(options.ip, options.virt)
    if status != PASS:
        logger.error("Error in calling get_host_info function")
        return FAIL

    host_cn = host_inst.CreationClassName
    host_sys = host_inst.Name

    assoc_cn = get_typed_class(options.virt, "HostedResourcePool")
    proc_cn  = get_typed_class(options.virt, "ProcessorPool")
    mem_cn   = get_typed_class(options.virt, "MemoryPool")
    net_cn = get_typed_class(options.virt, "NetworkPool")
    disk_cn = get_typed_class(options.virt, "DiskPool")
    poollist = { 
                 mem_cn : "MemoryPool/0", 
                 proc_cn : "ProcessorPool/0",
                 net_cn : "NetworkPool/%s" % default_network_name,
                 disk_cn : "DiskPool/%s" % default_pool_name
               }

    for k, v in poollist.items():
        try:
            assoc_host = AssociatorNames(options.ip, assoc_cn, k, InstanceID=v)
        except Exception:
            logger.error(Globals.CIM_ERROR_ASSOCIATORNAMES, assoc_cn)
            return FAIL
        if len(assoc_host) == 1:
            if assoc_host[0].keybindings['Name'] != host_sys:
                logger.error("Pool association returned wrong hostsystem")
                return FAIL
            if assoc_host[0].keybindings['CreationClassName'] != host_cn:
                logger.error("Pool assoc returned wrong CreationClassName")
                return FAIL

    return status
if __name__ == "__main__":
    sys.exit(main())
