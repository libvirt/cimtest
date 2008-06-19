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
from VirtLib import utils 
from CimTest.Globals import logger
from CimTest.Globals import do_main
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

def check_sched_info(str, exp_val, server, virt):
    if str == "limit":
        virsh_val = "cap"
    else:
        virsh_val = str

    cmd = "virsh -c %s schedinfo %s | awk '/%s/ { print \$3 }'" % \
          (utils.virt2uri(virt), default_dom, virsh_val)
    ret, out = utils.run_remote(server, cmd)
    if not out.isdigit():
        return FAIL

    try:
        val = int(out)
    except ValueError:
        val = -1

    if val != exp_val: 
        logger.error("%s is %i, expected %i" % (str, val, exp_val))
        return FAIL

    return PASS

def check_proc_sched(server, virt):
    attr_list = { "weight" : weight,
                  "limit"  : limit
                }
   
    for k, v in attr_list.iteritems():
        status = check_sched_info(k, v, server, virt)
        if status != PASS:
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

        status = poll_for_state_change(options.ip, options.virt, default_dom, 
                                       REQUESTED_STATE)
        if status != PASS:
            raise Exception("%s didn't change state as expected" % default_dom)

        if options.virt == "Xen" or options.virt == "XenFV":
            status = check_proc_sched(options.ip, options.virt)
            if status != PASS:
                raise Exception("%s CPU scheduling not set properly" % 
                                default_dom)

        status = PASS
      
    except Exception, details:
        logger.error(details)
        status = FAIL

    destroy_and_undefine_domain(default_dom, options.ip, options.virt)

    return status 

if __name__ == "__main__":
    sys.exit(main())
    
