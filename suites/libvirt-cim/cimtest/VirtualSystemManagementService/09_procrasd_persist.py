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
# Purpose:
#   Verify values for VirtualQuantity, limit and weight of ProcRASD are 
#   persisted properly over define/start/destroy sequence of the guest. 
#
# Steps:
#  1) Get the default rasds 
#  2) Set the ProcRASD VirtualQuantity, Weight, Limit, InstanceID values
#  3) Define the guest using the configuration
#  4) Verify the proc settings of the guest
#  5) start  the guest and verify the proc settings of the guest
#  6) Destroy and undefine the guest 
#  Repeat the Sequence 3 - 6 in loop to see that 
#  the VirtualQuantity, limit and weight are maintained as passed to
#  via the ProcRASD.
#

import sys
from pywbem.cim_types import Uint64, Uint32
from XenKvmLib.vxml import get_class
from XenKvmLib.enumclass import EnumInstances
from XenKvmLib.classes import get_typed_class, inst_to_mof
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import FAIL, PASS, XFAIL_RC
from XenKvmLib.rasd import get_default_rasds

libvirt_bug = '00013'
sup_types = ['Xen', 'XenFV', 'KVM']
test_dom = 'procrasd_persist_dom'

nvcpu = 3
weight = 124
limit = 512

def setup_guest(ip, virt, cxml, prasd_cn):
    rasds = get_default_rasds(ip, virt)
    rasd_list= { prasd_cn : None }
    
    for rasd in rasds:
        if rasd.classname == prasd_cn:
            rasd['InstanceID'] = '%s/proc' %test_dom
            rasd['VirtualQuantity'] = Uint64(nvcpu)
            rasd['Weight'] = Uint32(weight)
            rasd['Limit'] = Uint64(limit)
            rasd_list[prasd_cn] = inst_to_mof(rasd)

    if rasd_list[prasd_cn] is None:
        logger.error("Unable to set template ProcRASD")
        return FAIL

    cxml.set_res_settings(rasd_list)
    ret = cxml.cim_define(ip)
    if not ret:
        logger.error("Unable to define %s ", test_dom)
        return FAIL

    return PASS

def check_proc_sched(server, virt, cn_name):
    try:
        proc_rasd = None
        rasds = EnumInstances(server, cn_name, ret_cim_inst=True)
        for rasd in rasds:
            if test_dom in rasd["InstanceID"]:
                proc_rasd = rasd
                break

        if proc_rasd == None:
            logger.error("Did not find test RASD on server")
            return FAIL
   
        if proc_rasd["VirtualQuantity"] != nvcpu and virt != 'KVM':
            logger.error("VirtualQuantity is %s, expected %s",
                         proc_rasd["VirtualQuantity"], nvcpu)
            return FAIL
        elif proc_rasd["VirtualQuantity"] != nvcpu and virt == "KVM":
            return XFAIL_RC(libvirt_bug)

        if proc_rasd["Limit"] != limit:
            logger.error("Limit is %s, expected %s",
                         proc_rasd["Limit"], limit)
            return FAIL

        if proc_rasd["Weight"] != weight:
            logger.error("Weight is %s, expected %s",
                          proc_rasd["Weight"], weight)
            return FAIL

    except Exception, details:
        logger.error("Exception: details %s", details)
        return FAIL

    return PASS

@do_main(sup_types)
def main():
    options = main.options   
    virt = options.virt
    server = options.ip
    
    cxml = None
    prasd_cn = get_typed_class(virt, "ProcResourceAllocationSettingData")
    dom_define = dom_start = False
    try:
        for count in range(3):
            cxml = get_class(virt)(test_dom)
            status = setup_guest(server, virt, cxml, prasd_cn)
            if status != PASS:
                return status
    
            dom_define = True
            status = check_proc_sched(server, virt, prasd_cn)
            if status != PASS:
                raise Exception("CPU scheduling not set properly for "
                                " defined dom: %s" % test_dom)
        
            status = cxml.cim_start(server)
            if status != PASS:
                raise Exception("Unable to start %s " % test_dom)

            dom_start = True
            status = check_proc_sched(server, virt, prasd_cn)
            if status != PASS and virt != 'KVM':
                raise Exception("CPU scheduling not set properly for the dom: "
                                "%s" % test_dom)
            elif status != PASS and virt == 'KVM':
                break

            cxml.cim_destroy(server)
            dom_start = False

            cxml.undefine(server)
            dom_define = False
      
    except Exception, details:
        logger.error("Exception: details %s", details)
        status = FAIL

    if dom_start == True:
        cxml.cim_destroy(server)

    if dom_define == True: 
        cxml.undefine(server)
    
    return status 

if __name__ == "__main__":
    sys.exit(main())
    
