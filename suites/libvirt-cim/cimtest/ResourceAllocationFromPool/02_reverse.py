#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
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
from VirtLib import utils
from XenKvmLib import assoc
from XenKvmLib import devices
from XenKvmLib.devices import Xen_Memory, Xen_Processor
from CimTest import Globals
from CimTest.Globals import log_param, logger, do_main
from CimTest.ReturnCodes import PASS, FAIL, XFAIL

sup_types = ['xen']

@do_main(sup_types)
def main():
    options = main.options
    log_param()
    status = PASS

    key_list = ["DeviceID", "CreationClassName", "SystemName",
                "SystemCreationClassName"]
    try:
        mem = devices.enumerate(options.ip, Xen_Memory, key_list)
    except Exception:
        logger.error(Globals.CIM_ERROR_ENUMERATE % devices.Xen_Memory)
        return FAIL

    try:
        proc = devices.enumerate(options.ip, Xen_Processor, key_list)
    except Exception:
        logger.error(Globals.CIM_ERROR_ENUMERATE % devices.Xen_Processor)
        return FAIL
        
    for i in range(len(mem)):
        try:
            mempool = assoc.AssociatorNames(options.ip, "Xen_ResourceAllocationFromPool",
                                            "Xen_MemResourceAllocationSettingData", 
                                            InstanceID = mem[i].DeviceID)
        except Exception:
            logger.error(Globals.CIM_ERROR_ASSOCIATORNAMES % mem[i].DeviceID)
            status = FAIL

        if len(mempool) < 1:
            logger.error("No associated pool for %s" % mem[i].DeviceID)
            return FAIL

        if mempool[0].keybindings['InstanceID'] != "MemoryPool/0":
            logger.error("MemResourceAllocationSettingData association error")
            return FAIL
            
    for j in range(len(proc)):
        try:
            procpool = assoc.AssociatorNames(options.ip, "Xen_ResourceAllocationFromPool",
                                             "Xen_ProcResourceAllocationSettingData",
                                             InstanceID = proc[j].DeviceID)
        except Exception:
            logger.error(Globals.CIM_ERROR_ASSOCIATORNAMES % proc[j].DeviceID)
            return FAIL
            
        if len(procpool) < 1:
            logger.error("No associated pool for %s" % proc[j].DeviceID)
            return FAIL

        if procpool[0].keybindings['InstanceID'] != "ProcessorPool/0":
            logger.error("ProcResourceAllocationSettingData association failed")
            status = FAIL

    return status

if __name__ == "__main__":
    sys.exit(main())
