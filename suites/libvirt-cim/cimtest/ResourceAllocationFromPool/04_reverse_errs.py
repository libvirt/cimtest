#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
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
import pywbem
from pywbem.cim_obj import CIMInstanceName
from XenKvmLib import assoc
from XenKvmLib.classes import get_typed_class
from CimTest import Globals
from CimTest.Globals import log_param, logger, do_main
from CimTest.ReturnCodes import PASS, FAIL, XFAIL

sup_types = ['Xen', 'XenFV', 'KVM']

exp_rc = 6 #CIM_ERR_NOT_FOUND
exp_desc = "No such instance"

@do_main(sup_types)
def main():
    options = main.options
    log_param()
    rc = -1
    status = FAIL


    dataset = {get_typed_class(options.virt, "MemResourceAllocationSettingData") : "wrong", 
               get_typed_class(options.virt, "ProcResourceAllocationSettingData") : "wrong"}
    conn = assoc.myWBEMConnection('http://%s' % options.ip,                                        
                                  (Globals.CIM_USER, Globals.CIM_PASS),
                                  Globals.CIM_NS)
    for k, v in dataset.items():
        instanceref = CIMInstanceName(k, 
                                      keybindings = {"InstanceID" : v})
        names = []

        try:
            names = conn.AssociatorNames(instanceref, 
                                         AssocClass = get_typed_class(options.virt, "ResourceAllocationFromPool"))
            rc = 0
        except pywbem.CIMError, (rc, desc):
            if rc == exp_rc and desc.find(exp_desc) >= 0:
                logger.info("Got excepted rc code and error string")
                status = PASS
            else:
                logger.error("Unexpected rc code %s and description %s\n" %(rc, desc))
        except Exception, details:
            logger.error("Unknown exception happened")
            logger.error(details)

        if rc == 0:
            logger.error("ResourceAllocationSettingData should NOT return excepted result with a wrong InstanceID value of %s input" %k)
            status = FAIL
        
        return status        


if __name__ == "__main__":
    sys.exit(main())
