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
from XenKvmLib import assoc
from XenKvmLib import enumclass
from XenKvmLib.const import default_network_name
from CimTest import Globals
from CimTest.Globals import logger
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import do_main
from XenKvmLib.classes import get_typed_class
from XenKvmLib.common_util import cleanup_restore, create_diskpool_conf

sup_types=['Xen', 'KVM', 'XenFV', 'LXC']
@do_main(sup_types)
def main():
    options = main.options
    status = PASS

    status, dpool_name = create_diskpool_conf(options.ip, options.virt)
    if status != PASS:
        logger.error("Failed to create diskpool")
        return FAIL

    keys = ['Name', 'CreationClassName']
    try:
        host_sys = enumclass.enumerate(options.ip, 'HostSystem', keys, options.virt)[0]
    except Exception:
        host_cn = get_typed_class(options.virt, "HostSystem")
        logger.error(Globals.CIM_ERROR_ENUMERATE % host_cn)
        return FAIL 
    assoc_cn = get_typed_class(options.virt, "HostedResourcePool")
    proc_cn  = get_typed_class(options.virt, "ProcessorPool")
    mem_cn   = get_typed_class(options.virt, "MemoryPool")
    net_cn = get_typed_class(options.virt, "NetworkPool")
    disk_cn = get_typed_class(options.virt, "DiskPool")
    poollist = { 
                 mem_cn : "MemoryPool/0", 
                 proc_cn : "ProcessorPool/0",
                 net_cn : "NetworkPool/%s" %default_network_name,
                 disk_cn : "DiskPool/%s" %dpool_name
               }

    for k, v in poollist.items():
        try:
            assoc_host = assoc.AssociatorNames(options.ip, assoc_cn, k, InstanceID = v, \
                                                                     virt = options.virt)
        except Exception:
            logger.error(Globals.CIM_ERROR_ASSOCIATORNAMES % v)
            return FAIL
        if len(assoc_host) == 1:
            if assoc_host[0].keybindings['Name'] != host_sys.Name:
                logger.error("Pool association returned wrong hostsystem")
                status = FAIL 
            if assoc_host[0].keybindings['CreationClassName'] != host_sys.CreationClassName:
                logger.error("Pool association returned wrong CreationClassName")
                status = FAIL 
        if status != PASS:
            break 
    cleanup_restore(options.ip, options.virt) 
    return status
if __name__ == "__main__":
    sys.exit(main())
