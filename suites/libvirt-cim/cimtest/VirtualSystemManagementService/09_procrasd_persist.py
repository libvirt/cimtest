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

import sys
import pywbem
from XenKvmLib.common_util import call_request_state_change, \
                                  poll_for_state_change 
from XenKvmLib import vsms
from XenKvmLib.enumclass import GetInstance
from XenKvmLib.common_util import get_typed_class
from VirtLib import utils 
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import FAIL, PASS
from XenKvmLib.test_doms import destroy_and_undefine_domain 

sup_types = ['Xen', 'XenFV', 'KVM']
default_dom = 'rstest_domain'

nvcpu = 2
weight = 124
limit = 256

REQUESTED_STATE = 2
TIME = "00000000000000.000000:000"

def setup_rasd_mof(ip, vtype):
    vssd, rasd = vsms.default_vssd_rasd_str(default_dom, virt=vtype)

    class_pasd = vsms.get_pasd_class(vtype)
    proc_inst = class_pasd(nvcpu, default_dom, weight, limit) 
    proc_mof = proc_inst.mof()

    for i in range(len(rasd)):
        if "ProcResourceAllocationSettingData" in rasd[i]:
            rasd[i] = proc_mof
            return PASS, vssd, rasd

    return FAIL, vssd, rasd

def check_proc_sched(server, virt):
    try:
        key_list = {"InstanceID" : '%s/proc' %default_dom}
        cn_name  = get_typed_class(virt, 'ProcResourceAllocationSettingData')
        proc = GetInstance(server, cn_name, key_list)
   
        if proc.Limit != limit:
            logger.error("Limit is %i, expected %i", proc.Limit, limit)
            return FAIL

        if proc.Weight != weight:
            logger.error("Weight is %i, expected %i", proc.Weight, weight)
            return FAIL

    except Exception, details:
        logger.error("Exception: details %s", details)
        return FAIL

    return PASS

@do_main(sup_types)
def main():
    options = main.options

    status, vssd, rasd = setup_rasd_mof(options.ip, options.virt)
    if status != PASS:
        return status

    try:
        service = vsms.get_vsms_class(options.virt)(options.ip)
        service.DefineSystem(SystemSettings=vssd,
                             ResourceSettings=rasd,
                             ReferenceConfiguration=' ')

        rc = call_request_state_change(default_dom, options.ip,
                                       REQUESTED_STATE, TIME, options.virt)
        if rc != 0:
            raise Exception("Unable to start %s using RequestedStateChange()" %
                            default_dom)

        status, dom_cs = poll_for_state_change(options.ip, options.virt, 
                                               default_dom, REQUESTED_STATE)
        if status != PASS:
            raise Exception("%s didn't change state as expected" % default_dom)

        status = check_proc_sched(options.ip, options.virt)
        if status != PASS:
            raise Exception("%s CPU scheduling not set properly", default_dom)

        status = PASS
      
    except Exception, details:
        logger.error("Exception: details %s", details)
        status = FAIL

    destroy_and_undefine_domain(default_dom, options.ip, options.virt)

    return status 

if __name__ == "__main__":
    sys.exit(main())
    
