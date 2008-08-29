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
from XenKvmLib.enumclass import getInstance 
from XenKvmLib.assoc import Associators, compare_all_prop
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger, CIM_ERROR_ASSOCIATORS
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.vxml import get_class
from XenKvmLib.const import do_main 

sup_types = ['Xen', 'XenFV', 'KVM', 'LXC']

test_dom = "esd_dom"
vmac = "00:11:22:33:44:aa"

def get_inst(ip, virt, cn, key):
    inst = None 

    try:
        key_list = {"InstanceID" : key }

        inst = getInstance(ip, cn, key_list, virt)

    except Exception, details:
        logger.error("Exception %s" % details)
        return None 

    if inst is None:
        logger.error("Expected at least one %s instance" % cn)
        return None 

    return inst 


def test_assoc(host, acn, cn, virt, inst):
    id = inst.InstanceID

    try:
        ret_inst = Associators(host, acn, cn, virt, InstanceID=id)

    except Exception:
        logger.error(CIM_ERROR_ASSOCIATORS, acn)
        return FAIL

    if len(ret_inst) != 1:
        logger.error("%s returned %i %s instances" % (an, len(ret_inst), cn))
        return FAIL

    ret_id = ret_inst[0]['InstanceID']
    if ret_id != id:
        logger.error("%s returned %s inst with wrong id %s" % (acn, cn, ret_id))
        return FAIL

    status = compare_all_prop(ret_inst[0], inst)

    return status

@do_main(sup_types)
def main():
    options = main.options

    esd_cn = 'ElementSettingData'

    if options.virt == 'XenFV':
        virt_type = 'Xen'
    else:
        virt_type = options.virt

    keys = { 'VirtualSystemSettingData' : "%s:%s" % (virt_type, test_dom),
             'MemResourceAllocationSettingData' : "%s/mem" % test_dom,
           }
               

    if options.virt == "Xen":
        vdisk = "xvda"
    else:
        vdisk = "hda"

    virt_class = get_class(options.virt)
    if options.virt == 'LXC':
        cxml = virt_class(test_dom)
    else:
        cxml = virt_class(test_dom, mac = vmac, disk = vdisk)
        keys['ProcResourceAllocationSettingData'] = "%s/proc" % test_dom
        keys['DiskResourceAllocationSettingData'] = "%s/%s" % (test_dom, vdisk)
        keys['NetResourceAllocationSettingData'] = "%s/%s" % (test_dom, vmac)
               
    ret = cxml.define(options.ip)
    if not ret:
        logger.error("Failed to define the dom: %s", test_dom)
        return FAIL

    inst_list = {}

    for cn, k in keys.iteritems():
        inst_list[cn] = get_inst(options.ip, options.virt, cn, k)
        if inst_list[cn] is None:
            cxml.undefine(options.ip)
            return FAIL 

    status = FAIL
    for cn, inst in inst_list.iteritems():
        status = test_assoc(options.ip, esd_cn, cn, options.virt, inst)
        if status != PASS:
            logger.error("Unable to get %s insts from %s" % (cn, esd_cn))
            break
        
    cxml.undefine(options.ip)
        
    return status
                    
if __name__ == "__main__":
    sys.exit(main())
