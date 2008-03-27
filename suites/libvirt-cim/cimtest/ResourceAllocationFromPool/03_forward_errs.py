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
from CimTest import Globals
from CimTest.Globals import log_param, logger, do_main
from CimTest.ReturnCodes import PASS, FAIL, XFAIL

sup_types = ['Xen']

exp_rc = 6 #CIM_ERR_NOT_FOUND
exp_desc = "No such instance (wrong) - resource pool type mismatch"


@do_main(sup_types)
def main():
    options = main.options
    log_param()
    rc = -1
    status = FAIL


    poollist = {"Xen_MemoryPool" : "wrong", "Xen_ProcessorPool" : "wrong"}
    conn = assoc.myWBEMConnection('http://%s' % options.ip,                                        
                                  (Globals.CIM_USER, Globals.CIM_PASS),
                                  Globals.CIM_NS)
    for k, v in poollist.items():
        instanceref = CIMInstanceName(k, 
                                      keybindings = {"InstanceID" : v})
        names = []

        try:
            names = conn.AssociatorNames(instanceref, AssocClass = "Xen_ResourceAllocationFromPool")
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
        finally:
            if rc == 0:
                logger.error("ResourceAllocationFromPool associator should NOT return excepted result with a wrong InstanceID value of %s input" %k)
                status = FAIL
        
        return status        


if __name__ == "__main__":
    sys.exit(main())
