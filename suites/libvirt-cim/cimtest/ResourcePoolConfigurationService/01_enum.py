#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
#    Zhengang Li <lizg@cn.ibm.com>
#    Deepti B. Kalakeri<dkalaker@in.ibm.com>
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
from XenKvmLib import rpcs
from XenKvmLib.common_util import get_host_info
from CimTest import Globals
from CimTest.ReturnCodes import PASS, FAIL
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from XenKvmLib.classes import get_typed_class

platform_sup = ['Xen', 'XenFV', 'LXC', 'KVM']

@do_main(platform_sup)
def main():
    options = main.options
    server = options.ip
    classname =  get_typed_class(options.virt, "ResourcePoolConfigurationService")
    keys = ['Name', 'CreationClassName']
    status, host_inst = get_host_info(server, options.virt)
    if status != PASS:
        logger.error("Error in calling get_host_info function")
        return FAIL

    host_cn = host_inst.CreationClassName
    host_sys = host_inst.Name

    try:
        rpcservice = rpcs.enumerate(server, classname)
    except Exception:
        logger.error(Globals.CIM_ERROR_ENUMERATE, classname)
        return FAIL

    valid_service = {"Name" : "RPCS",
                     "CreationClassName" : classname,
                     "SystemCreationClassName" : host_cn,
                     "SystemName" : host_sys}

    if len(rpcservice) != 1:
        logger.error("Too many service error")
        return FAIL
    elif rpcservice[0].Name != valid_service["Name"]:
        logger.error("Rpcservice Name error")
        return FAIL
    elif rpcservice[0].CreationClassName != valid_service["CreationClassName"]:
        logger.error("Rpcservice CreationClassName error")
        return FAIL
    elif rpcservice[0].SystemCreationClassName != valid_service["SystemCreationClassName"]:
        logger.error("Rpcservice SystemCreationClassName error")
        return FAIL
    elif rpcservice[0].SystemName != valid_service["SystemName"]:
        logger.error("Rpcservice SystemName error")
        return FAIL
    return PASS

if __name__ == "__main__":
    sys.exit(main())
