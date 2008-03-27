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
from CimTest.ReturnCodes import PASS, FAIL, SKIP

sup_types = ['Xen']

exp_rc = 6 #CIM_ERR_NOT_FOUND
exp_desc = "No such instance"

def try_assoc(ref, ref_class, exp_rc, exp_desc, options):
    conn = assoc.myWBEMConnection('http://%s' % options.ip,
                                  (Globals.CIM_USER, Globals.CIM_PASS),
                                  Globals.CIM_NS)
    log_param()
    status = FAIL
    rc = -1
    names = []

    try:
        names = conn.AssociatorNames(ref, AssocClass = "Xen_ElementCapabilities")
        rc = 0
    except pywbem.CIMError, (rc, desc):
        if rc == exp_rc and desc.find(exp_desc) >= 0:
            logger.info("Got expected rc code and error string")
            status = PASS
        else:
            logger.error("Unexpected rc code %s and description %s\n" %(rc, desc))
    except Exception, details:
        logger.error("Unknown exception happened")
        logger.error(details)
    finally:
        if rc == 0:
            logger.error("Xen_ElementCapabilities associator should NOT return excepted result with a wrong key name and value of %s input" % ref_class)
            status = FAIL
    
    return status

@do_main(sup_types)
def main():
    rc = PASS
    cap_list = {"Xen_VirtualSystemManagementCapabilities" : "ManagementCapabilities",
                "Xen_VirtualSystemMigrationCapabilities" : "MigrationCapabilities"}

    for k, v in cap_list.items():
        instanceref = CIMInstanceName(k, 
                                      keybindings = {"InstanceID" : "wrong"})
        rc = try_assoc(instanceref, k, exp_rc, exp_desc, options)
        if rc != PASS:
            status = FAIL
            return status

    elecref = CIMInstanceName("Xen_EnabledLogicalElementCapabilities",
                              keybindings = {"InstanceID" : "wrong"})
    rc = try_assoc(elecref, "Xen_EnabledLogicalElementCapabilities",
                   exp_rc, exp_desc, options)
    if rc != PASS:
        status = FAIL
        return status

if __name__ == "__main__":
    sys.exit(main())
