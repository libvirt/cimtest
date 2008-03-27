#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Kaitlin Rupert <karupert@us.ibm.com>
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

# This test case passes both VSSD and RASD instances to the ElementSettingData 
# association provider.

# Steps:
#  1. Enum VirtualSystemSettingData. 
#  2. For each VSSD returned, test its associations via ElementSettingData.
#  3. For each VSSD returned, get its associated RASD instances via  
#     VirtualSystemSettingDataComponent
#  4. For each RASD returned, test its associations via ElementSettingData.
#

# Example VSSD command:
#
# wbemcli ain -ac Xen_ElementSettingData -arc Xen_VirtualSystemSettingData 'http://localhost/root/virt:Xen_VirtualSystemSettingData.InstanceID="Xen:Domain-0"'
#
# Output:
# localhost:5988/root/virt:Xen_VirtualSystemSettingData.InstanceID="Xen:Domain-0"
#

# Example RASD command:
#
# wbemcli ain -ac Xen_ElementSettingData 'http://localhost/root/virt:Xen_ProcResourceAllocationSettingData.InstanceID="Domain-0/0"'
#
# Output:
#localhost:5988/root/virt:Xen_ProcResourceAllocationSettingData.InstanceID="Domain-0/0"
#

import sys
from VirtLib import utils
from XenKvmLib import enumclass
from XenKvmLib import assoc
from CimTest import Globals
from CimTest.Globals import do_main

sup_types = ['Xen']

def test_assoc(host, class_name, id):
    try:
        ret_inst = assoc.AssociatorNames(host,
                                         "Xen_ElementSettingData",
                                         class_name,
                                         InstanceID = id)
    except Exception:
        Globals.logger.error(Globals.CIM_ERROR_ASSOCIATORS,
                             'Xen_ElementSettingData')
        return 1

    if len(ret_inst) != 1:
        Globals.logger.error("Xen_ElementSettingData returned %i %s instances",
                             len(ret_inst),
                             class_name)
        return 1

    ret_id = ret_inst[0].keybindings["InstanceID"]
    if ret_id != id:
        Globals.logger.error("%s returned %s instance with wrong id %s",
                             "Xen_ElementSettingData",
                             class_name,
                             ret_id) 
        return 1

    return 0;

@do_main(sup_types)
def main():
    options = main.options
    Globals.log_param()

    try:
        key_list = ["InstanceID"]
        vssd_lst = enumclass.enumerate(options.ip,
                                       enumclass.Xen_VirtualSystemSettingData,
                                       key_list)

    except Exception, details:
        Globals.logger.error("Exception %s", details)
        return 1

    for vssd in vssd_lst:

        rc = test_assoc(options.ip, 
                        "Xen_VirtualSystemSettingData", 
                        vssd.InstanceID)
        if rc != 0:
            Globals.logger.error("Unable to get associated %s from %s",
                                 "Xen_VirtualSystemSettingData",
                                 "Xen_ElementSettingData")
            return 1
        
        try:
            rasd_list = assoc.Associators(options.ip,
                                        "Xen_VirtualSystemSettingDataComponent",
                                        "Xen_VirtualSystemSettingData",
                                        InstanceID = vssd.InstanceID)
        except Exception:
            Globals.logger.error(Globals.CIM_ERROR_ASSOCIATORS,
                                 'Xen_VirtualSystemSettingDataComponent')
            return 1

        if len(rasd_list) == 0:
            Globals.logger.error("%s returned %i %s instances",
                                 "Xen_ElementSettingData",
                                 len(rasd_list),
                                 "Xen_VirtualSystemSettingData")
            return 1

        for rasd in rasd_list:
            rc = test_assoc(options.ip, 
                            rasd.classname, 
                            rasd["InstanceID"])
            if rc != 0:
                Globals.logger.error("Unable to get associated %s from %s",
                                     "Xen_ResourceAllocationSettingData",
                                     "Xen_ElementSettingData")
                return 1
        
    return 0
                    
if __name__ == "__main__":
    sys.exit(main())
