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
from XenKvmLib import hostsystem
from XenKvmLib.classes import get_typed_class
from CimTest import Globals
from CimTest.Globals import logger, do_main
from CimTest.ReturnCodes import PASS, FAIL, XFAIL

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']
exp_rc = 6 #CIM_ERR_NOT_FOUND
exp_desc = "No such instance"

@do_main(sup_types)
def main():
    options = main.options
    rc = -1
    status = FAIL

    try:
        host_sys = hostsystem.enumerate(options.ip, options.virt)[0]
    except Exception:
        logger.error(Globals.CIM_ERROR_ENUMERATE % host_sys.name)
        return FAIL


    servicelist = {get_typed_class(options.virt, "ResourcePoolConfigurationService") : "RPCS",
                   get_typed_class(options.virt, "VirtualSystemManagementService") : "Management Service",
                   get_typed_class(options.virt, "VirtualSystemMigrationService") : "MigrationService"}
                                              
    
    conn = assoc.myWBEMConnection('http://%s' % options.ip,                                        
                                  (Globals.CIM_USER, Globals.CIM_PASS),
                                  Globals.CIM_NS)
    for k, v in servicelist.items():
        instanceref = CIMInstanceName(k, 
                                      keybindings = {"Wrong" : v,
                                                     "CreationClassName" : "wrong",
                                                     "SystemCreationClassName" : host_sys.CreationClassName,
                                                     "SystemName" : host_sys.Name})
        names = []

        try:
            names = conn.AssociatorNames(instanceref, AssocClass = get_typed_class(options.virt, "HostedService"))
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
            logger.error("HostedService associator should NOT return excepted result with a wrong key name and value of %s input" % k)
            status = FAIL
                
        return status        


if __name__ == "__main__":
    sys.exit(main())
