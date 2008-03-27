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
from VirtLib import utils
from VirtLib import live
from XenKvmLib import assoc
from XenKvmLib import hostsystem
from CimTest import Globals
from CimTest.Globals import do_main
from CimTest.ReturnCodes import PASS, FAIL, SKIP

sup_types = ['Xen']

@do_main(sup_types)
def main():
    options = main.options
    Globals.log_param()

    try:
        host_sys = hostsystem.enumerate(options.ip)[0]
    except Exception:
        Globals.logger.error(Globals.CIM_ERROR_ENUMERATE, 'Xen_HostSystem')
        return FAIL

    try:
        elc = assoc.AssociatorNames(options.ip,
                                     "Xen_ElementCapabilities",
                                     "Xen_HostSystem", 
                                     Name = host_sys.Name,
                                     CreationClassName = host_sys.CreationClassName)
    except Exception:
        Globals.logger.error(Globals.CIM_ERROR_ASSOCIATORNAMES % host_sys.Name)
        return FAIL


    valid_elc_name = ["Xen_VirtualSystemManagementCapabilities",
                      "Xen_VirtualSystemMigrationCapabilities"]
    valid_elc_id = ["ManagementCapabilities", 
                    "MigrationCapabilities"]

    if len(elc) == 0:
        Globals.logger.error("ElementCapabilities association failed, excepted at least one instance")
        return FAIL
    for i in range(0,len(elc)):
        if elc[i].classname not in valid_elc_name:
            Globals.logger.error("ElementCapabilities association classname error")
            return FAIL
        elif elc[i].keybindings['InstanceID'] not in valid_elc_id:
            Globals.logger.error("ElementCapabilities association InstanceID error")
            return FAIL


    cs = live.domain_list(options.ip)
    for system in cs:  
        try:
	    elec = assoc.AssociatorNames(options.ip,
                                         "Xen_ElementCapabilities",
                                         "Xen_ComputerSystem",
                                         Name = system,
                                         CreationClassName = "Xen_ComputerSystem")
  	except Exception:
            Globals.logger.error(Globals.CIM_ERROR_ASSOCIATORNAMES % system)
            return FAIL     
         
        if elec[0].classname != "Xen_EnabledLogicalElementCapabilities":
	    Globals.logger.error("ElementCapabilities association classname error")
            return FAIL
        elif elec[0].keybindings['InstanceID'] != system:
            Globals.logger.error("ElementCapabilities association InstanceID error")
            return FAIL

if __name__ == "__main__":
    sys.exit(main())
