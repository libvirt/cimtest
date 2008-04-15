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
from XenKvmLib.classes import get_class_basename
from CimTest import Globals
from CimTest.Globals import do_main

sup_types = ['Xen', 'KVM']
esd_cn = 'ElementSettingData'
vssd_cn = 'VirtualSystemSettingData'
vssdc_cn = 'VirtualSystemSettingDataComponent'
rasd_cn = 'ResourceAllocationSettingData'

def test_assoc(host, class_name, id, virt):
    try:
        ret_inst = assoc.AssociatorNames(host,esd_cn, class_name, virt,
                                         InstanceID = id)
    except Exception:
        Globals.logger.error(Globals.CIM_ERROR_ASSOCIATORS, esd_cn)
        return 1

    if len(ret_inst) != 1:
        Globals.logger.error("%s returned %i %s instances", esd_cn,
                             len(ret_inst), class_name)
        return 1

    ret_id = ret_inst[0].keybindings["InstanceID"]
    if ret_id != id:
        Globals.logger.error("%s returned %s instance with wrong id %s",
                             esd_cn, class_name, ret_id) 
        return 1

    return 0;

@do_main(sup_types)
def main():
    options = main.options
    Globals.log_param()

    try:
        key_list = ["InstanceID"]
        vssd_lst = enumclass.enumerate(options.ip, vssd_cn, key_list,
                                       options.virt)

    except Exception, details:
        Globals.logger.error("Exception %s", details)
        return 1

    for vssd in vssd_lst:

        rc = test_assoc(options.ip, vssd_cn, vssd.InstanceID, options.virt)
        if rc != 0:
            Globals.logger.error("Unable to get associated %s from %s",
                                 vssd_cn, esd_cn)
            return 1
        
        try:
            rasd_list = assoc.Associators(options.ip, vssdc_cn, vssd_cn,
                                          options.virt, 
                                          InstanceID = vssd.InstanceID)
        except Exception:
            Globals.logger.error(Globals.CIM_ERROR_ASSOCIATORS, vssdc_cn)
            return 1

        if len(rasd_list) == 0:
            Globals.logger.error("%s returned %i %s instances", esd_cn,
                                 len(rasd_list), vssd_cn)
            return 1

        for rasd in rasd_list:
            rc = test_assoc(options.ip, get_class_basename(rasd.classname),
                            rasd["InstanceID"], options.virt)
            if rc != 0:
                Globals.logger.error("Unable to get associated %s from %s",
                                     rasd_cn, esd_cn)
                return 1
        
    return 0
                    
if __name__ == "__main__":
    sys.exit(main())
