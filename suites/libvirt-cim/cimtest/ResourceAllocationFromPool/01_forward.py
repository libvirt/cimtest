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
from XenKvmLib import enumclass
from XenKvmLib.classes import get_typed_class 
from CimTest import Globals
from CimTest.Globals import log_param, logger, do_main
from CimTest.ReturnCodes import PASS, FAIL, XFAIL

sup_types = ['Xen', 'XenFV', 'KVM']

@do_main(sup_types)
def main():
    options = main.options
    log_param()
    status = PASS

    try:
        key_list = { 'InstanceID' : "MemoryPool/0" }
        mempool = enumclass.getInstance(options.ip,
                                        "MemoryPool",
                                        key_list,
                                        options.virt)
    except Exception:
        logger.error(Globals.CIM_ERROR_GETINSTANCE  % "MemoryPool")
        return FAIL

    try:
        key_list = { 'InstanceID' : "ProcessorPool/0" }
        procpool = enumclass.getInstance(options.ip,
                                         "ProcessorPool",
                                         key_list,
                                         options.virt)
    except Exception:
        logger.error(Globals.CIM_ERROR_GETINSTANCE % "ProcessorPool")  
        return FAIL
     
    try:
        memdata = assoc.AssociatorNames(options.ip, "ResourceAllocationFromPool",
                                        "MemoryPool",
                                        options.virt,
                                        InstanceID = mempool.InstanceID)
    except Exception:
        logger.error(Globals.CIM_ERROR_ASSOCIATORNAMES % mempool.InstanceID)
        status = FAIL
     
    for i in range(len(memdata)):
        if memdata[i].classname != get_typed_class(options.virt, "MemResourceAllocationSettingData"):
            logger.error("ERROR: Association result error")
            status = FAIL
                
    try:
        procdata = assoc.AssociatorNames(options.ip, "ResourceAllocationFromPool",
                                         "ProcessorPool",
                                         options.virt,
                                         InstanceID = procpool.InstanceID)
    except Exception:
        logger.error(Globals.CIM_ERROR_ASSOCIATORNAMES % procpool.InstanceID)
        status = FAIL
      
    for j in range(len(procdata)):
        if procdata[j].classname != get_typed_class(options.virt, "ProcResourceAllocationSettingData"):
	    logger.error("ERROR: Association result error")
            status = FAIL

    return status 
        
        
if __name__ == "__main__":
    sys.exit(main())
